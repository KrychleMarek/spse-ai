import re
from pathlib import Path
import json

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Klíčová slova pro rozpoznání předmětových nadpisů
subject_heading_keywords = [
    "Co se naučím v",
    "Co se učí 1.",
    "Co se učí 2.",
    "Co se učí 3.",
    "Co se učí 4.",
]

# Regulární výraz pro rozpoznání hlavních nadpisů v upraveném dokumentu
heading_pattern = re.compile(
    r"^(Základní informace o oboru|Profil absolventa|Uplatnění absolventa|"
    r"Klíčové dovednosti a kompetence|Organizace výuky a praktické příležitosti|"
    r"Hodnocení žáků|JAKÉ PŘEDMĚTY JSOU/SE VYUČUJÍ NA OBORU|"
    r"Co se naučím v\s+.*?|Co se učí [1-4]\.\s*ročník v)",
    re.IGNORECASE
)

# Funkce pro extrakci názvu předmětu z nadpisu
def extract_subject_from_heading(heading: str) -> str | None:
    # Zkontroluj, zda nadpis obsahuje některé z předmětových klíčových slov
    if not any(keyword.lower() in heading.lower() for keyword in subject_heading_keywords):
        return None  # Nejedná se o předmětový nadpis

    # Odstraň úvodní část nadpisu (např. "Cíl předmětu", "Co se učí 1. ročník", apod.)
    cleaned = re.sub(
        r"^(Co se naučím v|"
        r"Co se učí \d\.\s*ročník)(?:\s+v)?(?:\s+předmětu)?",
        "",
        heading,
        flags=re.IGNORECASE
    ).strip(":：–—. ")

    # Odstraň případná zakončení jako "forma", "obsah", apod.
    cleaned = re.sub(
        r"\s+(důležitý|důležitá|forma|obsah|zaměření|typ|způsob)$",
        "",
        cleaned,
        flags=re.IGNORECASE
    ).strip()

    return cleaned if cleaned else None  # Pokud je něco vyčištěného, vrať to

# Funkce pro určení typu bloku podle nadpisu
def determine_chunk_type(heading: str) -> str:
    h = heading.lower()
    if any(keyword.lower() in h for keyword in subject_heading_keywords):
        return "předmět"  # Předmětová část
    elif any(h.startswith(s) for s in [
        "základní informace o oboru",
        "profil absolventa",
        "uplatnění absolventa",
        "klíčové dovednosti",
        "organizace výuky",
        "jaké předměty",
        "nadstandartní aktivity" 
    ]):
        return "obor"  # Obecné informace o oboru
    elif "hodnocení žáků" in h:
        return "meta"  # Metainformace o hodnocení
    else:
        return "unknown"  # Neznámý typ
                                                                                    
# Funkce pro rozdělení textového souboru na bloky (metadata chunky) podle nadpisů                     
def chunk_file_by_headings(path):
    chunks = []
    buffer = []
    prev_heading = None
    prev_subject = None
    prev_type = None
    source_file = Path(path).name

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        text = line.strip().replace('\uf0b7', '•')
        if not text:
            continue

        if heading_pattern.match(text):
            if prev_heading and buffer:
                chunk_text = "\n".join(buffer)
                chunks.append({
                    "text": f"{prev_heading}\n{chunk_text}",
                    "heading": prev_heading,
                    "subject": prev_subject,
                    "type": prev_type,
                    "source_file": source_file
                })
                buffer = []

            full_heading = text
            subject = extract_subject_from_heading(full_heading)
            
            chunk_type = determine_chunk_type(full_heading)

            prev_heading = full_heading
            prev_subject = subject
            prev_type = chunk_type
        else:
            buffer.append(text)

    if prev_heading and buffer:
        chunk_text = "\n".join(buffer)
        chunks.append({
            "text": f"{prev_heading}\n{chunk_text}",
            "heading": prev_heading,
            "subject": prev_subject,
            "type": prev_type,
            "source_file": source_file
        })

    return chunks

# Testování skriptu – spustí se pouze při přímém spuštění souboru
if __name__ == "__main__":
    path = ROOT_DIR / "data" / "processed" / "txtFiles" / "2025 SVP IoT Kopie.txt"  # Testovací soubor
    chunks = chunk_file_by_headings(path)  # Rozdělení na chunky

    print(f"Chunked into {len(chunks)} chunks.\n")
    for i, chunk in enumerate(chunks[:5], 1):  # Ukázka prvních 5 chunků
        print(f"--- Chunk {i} ---")
        print(f"Subject: {chunk['subject']}")
        print(f"Heading: {chunk['heading']}")
        print(f"Preview:\n{chunk['text'][:300]}...\n")

    # Uložení všech chunků do JSON souboru
    with open("kb_chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)