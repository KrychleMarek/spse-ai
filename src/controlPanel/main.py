# Backend aplikace ve FastAPI
import os
from qdrant_client import QdrantClient 
from qdrant_client.http.models import SearchParams
from collections import defaultdict
from typing import List
import shutil
import subprocess
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.datastructures import FormData, UploadFile

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "raw"
EMBEDD_DIR = BASE_DIR / "data" / "processed" / "embeddFiles"
EXTRACTDOCX_SCRIPT = BASE_DIR / "src" / "controlPanel" / "extractDocx.py"
EMBEDSVP_SCRIPT = BASE_DIR / "src" / "controlPanel" / "embedder.py"

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost") 
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", 6333))

qdrant_client = None

# Middleware pro CORS
# Umožňuje přístup z frontendu běžícího na localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # povolené domény
    allow_credentials=True,
    allow_methods=["*"],  # povolí všechny HTTP metody (GET, POST, ...)
    allow_headers=["*"],  # povolí všechny hlavičky
)

# Připojení statických souborů (např. CSS, JS, HTML)
app.mount("/controlPanel",
    StaticFiles(directory=BASE_DIR / "static" / "controlPanel"), # 
    name="static")

# Root endpoint: slouží jako UI (vrací index.html)
@app.get("/")
async def serve_ui():
    with open("static/controlPanel/index.html", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/embed/", response_class=HTMLResponse)
async def serve_extract_embed_ui():
    try:
        with open("static/controlPanel/extractEmbed.html", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>404: extractEmbed.html not found</h1>", status_code=404)

@app.get("/api/collections")
async def get_c_data():
    try:
        collections_data = fetch_existing_c()
        return JSONResponse(content=collections_data, status_code=200)
    except Exception as e:
        print(f"Error fetching collections: {e}")
        return JSONResponse(
            content={"error": "Failed to retrieve collections data."},
            status_code=500
        )

@app.get("/api/extractSvp")
async def get_ex_svp():
    try:
        extractSvp = fetch_extract_svp()
        return JSONResponse(content=extractSvp, status_code=200)
    except Exception as e:
        print(f"Error fetching svp for extraction: {e}")
        return JSONResponse(
            content={"error": "Failed to retrieve svp for extraction."},
            satus_code=500
        )

@app.get("/api/embeddSvp")
async def get_em_svp():
    try:
        embeddSvp = fetch_embedd_svp()
        return JSONResponse(content=embeddSvp, status_code=200)
    except Exception as e:
        print(f"Error fetch svp for embedding: {e}")
        return JSONResponse(
            content={"error": "Failed to retrieve svp for embedding."}
        )


@app.delete("/api/collections/{name}")
def delete_c(name: str):
    delete_c(name)
    return {"status": "ok"}

@app.delete("/api/extractSvp/{name}")
def delete_w_svp(name: str):
    delete_w(name)
    return {"status": "ok"}

@app.delete("/api/embeddSvp/{name}")
def delete_e_svp(name: str):
        delete_e(name)
        return {"status": "ok"}

@app.post("/api/uploadfile/")
async def create_upload_file(request: Request):
    
    uploaded_summary = {}
    
    form_data: FormData = await request.form()

    for subject_name, value in form_data.items():
        
        if isinstance(value, UploadFile):
            file: UploadFile = value
            
            original_extension = Path(file.filename).suffix
            
            new_filename = f"{subject_name}{original_extension}"
            
            file_path = UPLOAD_DIR / new_filename
            
            if file_path.exists(): # Odstraní původní soubor pokuď existuje v případě že se uživatel rozhodne změnit soubor 
                try:
                    file_path.unlink()
                    uploaded_summary[subject_name] = f"Existing file deleted. "
                except Exception as e:
                    print(f"Error deleting existing file {new_filename}: {e}")
                    uploaded_summary[subject_name] = f"Error deleting existing file: {e}"
                    

            try:
                contents = await file.read()
                
                with open(file_path, "wb") as buffer:
                    buffer.write(contents)
                
                uploaded_summary[subject_name] = f"Saved as: {new_filename}"
                
            except Exception as e:
                print(f" Error saving file for '{subject_name}' ('{file.filename}'): {e}")
                uploaded_summary[subject_name] = f"Error saving file: {e}"
            finally:
                await file.close()

    if not uploaded_summary:
        print("Received form data but found no UploadFile objects.")
       
        
        return {
            "message": "Files saved and renamed successfully. (No files found to process)",
            "results": uploaded_summary
        }
        
    return {
        "message": "Soubry úspěšně přijaty. Pokračujte v E&E.",
        "results": uploaded_summary
    }

@app.get("/api/extractAllSvp/")
async def startExtraction():
    extract_all_svp()
    delete_all_w_svp()
    return {"message": "Started extraction"}

@app.get("/api/embeddAllSvp")
async def startEmbedding():
    embedd_all_svp()
    delete_all_e_svp()
    return {"message": "Started embedding"}

def get_qdrant_client():
    #Vrátí instanci QDrant klienta, inicializuje ho, pokud neni.
    global qdrant_client
    
    if qdrant_client is None:
        #Provede se až je kód spuštěn v dockeru.
        qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    return qdrant_client

def fetch_existing_c():
    collections = {} 
    qdrant_client = get_qdrant_client()
    response = qdrant_client.get_collections()

    collection_names = [collection.name for collection in response.collections]

    for c in collection_names:
        collection_info = qdrant_client.get_collection(c)
        
        full_metadata = collection_info.config.metadata

        
        status = collection_info.status
        source_file = full_metadata.get("source_file")
        creation_date = full_metadata.get("creation_date")

        collections[c] = {
            "status": status,
            "source_file": source_file,
            "date": creation_date 
        }
        
    return collections

def fetch_extract_svp(): #Typuju že po konverzi souborů pudu maza soubory z /data/raw
    extractSvp = [
        path.stem for path in UPLOAD_DIR.glob('*.docx')
    ]
    return extractSvp

def fetch_embedd_svp():
    embeddSvp = [
        path.stem for path in EMBEDD_DIR.glob('*.docx')
    ]
    return embeddSvp

def delete_c(c_name):
    qdrant_client = get_qdrant_client()
    qdrant_client.delete_collection(collection_name=f"{c_name}")

def delete_w(svp_name):
    POSTFIX = ".docx"
    
    file_path = UPLOAD_DIR / f"{svp_name}{POSTFIX}"
    if file_path.exists():
                try:
                    file_path.unlink()
                    print(f"Existing file {file_path} deleted")
                except Exception as e:
                    print(f"Error deleting existing file {file_path}: {e}")

def delete_e(svp_name):
    POSTFIX = ".docx"
    
    file_path = EMBEDD_DIR / f"{svp_name}{POSTFIX}"
    if file_path.exists():
                try:
                    file_path.unlink()
                    print(f"Existing file {file_path} deleted")
                except Exception as e:
                    print(f"Error deleting existing file {file_path}: {e}")
    
def extract_all_svp():
    result = subprocess.run(["python", EXTRACTDOCX_SCRIPT], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Error output:\n", result.stderr)

def delete_all_w_svp():
    file_path = UPLOAD_DIR
    
    for f in file_path.glob("*.docx"):
        try:
            f.unlink()
            print(f"Deleted: {f.name}")
        except Exception as e:
            print(f"Error deleting {f.name}: {e}")

def embedd_all_svp():
    result = subprocess.run(["python", EMBEDSVP_SCRIPT], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Error output:\n", result.stderr)

def delete_all_e_svp():
    file_path = EMBEDD_DIR
    
    for f in file_path.glob("*.docx"):
        try:
            f.unlink()
            print(f"Deleted: {f.name}")
        except Exception as e:
            print(f"Error deleting {f.name}: {e}")