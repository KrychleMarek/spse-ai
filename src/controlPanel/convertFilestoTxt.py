from pathlib import Path
from docx import Document

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

INPUT_FOLDER = ROOT_DIR / "data" / "processed" / "embeddFiles"  # Složka se vstupníma .docx soubory
OUTPUT_FOLDER = ROOT_DIR / "data" / "processed" / "txtFiles"  # Složka kam se uloží .txt soubory
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True) 

def cleanup_output_folder(folder: Path, extension: str = "*.txt"):
    # Použijeme glob pro nalezení všech .txt souborů
    for file_to_delete in folder.glob(extension):
        file_to_delete.unlink() # Smazání

def convertToTxt():

    cleanup_output_folder(OUTPUT_FOLDER, "*.txt")

    # Pro každý .docx soubor ve složce ragFiles_folder
    for file_path in INPUT_FOLDER.glob("*.docx"):
            # Vytvoří odpovídající název .txt souboru
            txt_filename = file_path.stem + ".txt"
            txt_path = OUTPUT_FOLDER / txt_filename  # Sestaví cestu pro .txt soubor
            # Pokud .txt soubor neexistuje začne extrakci
            if not txt_path.exists():
                print(f"Extracting {file_path.name}", end="")  # Info pro uživatele
                doc = Document(file_path)  # Načte dokument
                # Sloučí text ze všech odstavců do jednoho řetězce
                full_text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
                # Uloží text do .txt souboru s UTF-8 kódováním
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(full_text)
                print(" done.") 