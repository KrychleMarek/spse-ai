import os
import datetime
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import numpy as np  # Matice
from sentence_transformers import SentenceTransformer  
from chunker import chunk_file_by_headings  
from pathlib import Path  
from convertFilestoTxt import convertToTxt  
from collections import defaultdict  # Slovník s výchozími hodnotami
import re  


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
c_path = ROOT_DIR / "data" / "processed" / "txtFiles" 

# SentenceTransformer("Seznam/dist-mpnet-czeng-cs-en")

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost") 
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", 6333))

qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

MODEL_PATH = "./models/seznam-mpnet-v1"

model = SentenceTransformer(MODEL_PATH) 

convertToTxt()  # Spustí převod všech dokumentů ve složce ./ragFiles

# Inicializace slovníků
subject_chunks = defaultdict(list)  # Uchovává textové bloky podle předmětu
subject_files = defaultdict(set)


# Zpracování všech .txt souborů
for file_path in c_path.glob("*.txt"):

    # Rozdělení textu na bloky podle nadpisů
    chunks = chunk_file_by_headings(file_path)
    subject_chunks[file_path.name].extend(chunks)
    subject_files[file_path.name] = file_path.name

# Embedding a uložení pro každý předmět
for subject_name in subject_files:
    chunks = subject_chunks[subject_name]
    file_name = subject_files[subject_name]
    if not chunks:
        print(f"No chunks found for {subject_name}, skipping...")
        continue

    print(f"Embedding {len(chunks)} chunks for {subject_name.upper()}...")

    metadata = {
        "creation_date" : datetime.datetime.now().strftime("%d-%m-%Y"),
        "source_file" : file_name
    }

    texts = [chunk.get('heading','') for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    dimension = embeddings.shape[1]
       
    #QDrant kolekce
    collection_name = subject_name.removesuffix(".txt")
    
    if qdrant_client.collection_exists(collection_name=collection_name):
        qdrant_client.delete_collection(collection_name=collection_name)
        print(f"  -> Kolekce '{collection_name}' smazána.")

    try:
        #Nové kolekce
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            metadata=metadata
        )
        print(f"  -> Kolekce '{collection_name}' vytvořena.")
    except Exception as e:
        print(f"  -> CHYBA při vytváření kolekce {collection_name}: {e}")
        continue
        
    #Příprava a nahrání bodů (PointStructs)
    points = []

    for idx, chunk in enumerate(chunks):
        # Payload (metadata)
        payload = {
            "heading": chunk.get('heading'),
            "text": chunk.get('text'),
            "model_name": MODEL_PATH,
            "source_file": file_name
        }

        points.append(
            PointStruct(
                id=idx, 
                vector=embeddings[idx].tolist(), # Vektor převedený na Python list
                payload=payload
            )
        )

    # Nahrani
    print(f"  -> Nahrávám {len(points)} bodů do QDrant...")
    operation_info = qdrant_client.upsert(
        collection_name=collection_name,
        points=points,
        wait=True
    )

    print(f"  -> Nahrání dokončeno. Status: {operation_info.status.value}")

print("\nVšechny kolekce byly úspěšně vytvořeny.")