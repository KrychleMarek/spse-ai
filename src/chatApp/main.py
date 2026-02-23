# Backend aplikace ve FastAPI
import os
from pathlib import Path
from fastapi import FastAPI
from qdrant_client import QdrantClient 
from qdrant_client.http.models import SearchParams
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .chat_rag import run_query  # Funkce pro zpracování dotazu pomocí RAG

# Inicializace FastAPI aplikace
app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

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
app.mount("/chatApp",
    StaticFiles(directory=BASE_DIR / "static" / "chatApp"), # 
    name="static")

# Root endpoint: slouží jako UI (vrací index.html)
@app.get("/")
async def serve_ui():
    with open("static/chatApp/index.html", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

# Mapování zobrazovaných názvů oborů na klíče používané v systému

# Model požadavku na /api/chat endpoint
class ChatRequest(BaseModel):
    question: str                     # otázka položená uživatelem
    selected_tag: str                 # vybraný obor (např. "IT-FP")
    chat_history: list[dict] = []    # historie předchozí konverzace

# Endpoint pro zpracování dotazu uživatele
@app.post("/api/chat")
@app.post("/api/chat/")  
async def chat_api(request: ChatRequest):
    
    collection_key = request.selected_tag
    query = request.question.strip()[:200] # Pojistka že text nebude delší než 200 písmen
    print("Zkrácené query: " + query)
    # Zavolání funkce run_query, která provede dotaz na znalostní bází
    answer = await run_query(request.question.strip(), collection_key, request.chat_history)

    # Vrácení odpovědi jako JSON
    return answer

@app.get("/api/collections")
async def get_collections_data():
    try:
        collections = fetch_existing_c()
        return JSONResponse(content=collections, status_code=200)
    except Exception as e:
        print(f"Error fetching collections: {e}")
        return JSONResponse(
            content={"error": "Failed to retrieve collections data."},
            status_code=500
        )

def get_qdrant_client():
    #Vrátí instanci QDrant klienta, inicializuje ho, pokud neni.
    global qdrant_client
    
    if qdrant_client is None:
        #Provede se až je kód spuštěn v dockeru.
        qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    return qdrant_client 


def fetch_existing_c():
    qdrant_client = get_qdrant_client()
    response = qdrant_client.get_collections()

    collections_keys = [collection.name for collection in response.collections]
    
    print(collections_keys)

    return collections_keys