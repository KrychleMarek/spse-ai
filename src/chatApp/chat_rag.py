import os
import logging
import asyncio
import json
from pathlib import Path

import numpy as np
import torch
import tiktoken
from qdrant_client import models as qmodels
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import SearchParams
from pylate import models, rank  # Správný import pro pylate
from sentence_transformers import SentenceTransformer
from openai import AsyncOpenAI

# --- Logování ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Načtení API klíče z config.json

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost") 
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", 6333))

qdrant_client = None
_client_lock = asyncio.Lock()

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

CONFIG_PATH = ROOT_DIR / "config.json"

with open(CONFIG_PATH) as f:
    config = json.load(f)

client = AsyncOpenAI(api_key=config["api_key"])

# embed_model = SentenceTransformer("Seznam/dist-mpnet-czeng-cs-en")
embed_model = SentenceTransformer("./models/seznam-mpnet-v1")

print("Model načten!")

colbert_model = models.ColBERT(
    model_name_or_path="lightonai/colbertv2.0",
    device="cpu"
)

encoding = tiktoken.get_encoding("cl100k_base")
def count_tokens(text): return len(encoding.encode(text))

# Config logování 
logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger(__name__)

async def get_qdrant_client():
    global qdrant_client
    if qdrant_client is None:
        async with _client_lock:
            if qdrant_client is None:
                logger.info("Initializing Async Qdrant client")
                qdrant_client = AsyncQdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    return qdrant_client

# Načtení znalostní báze ze souborů podle klíče 
async def check_c_exists(c_key: str) -> str:
    qdrant_client = await get_qdrant_client()
    collection_name = c_key 
    try:
        await qdrant_client.get_collection(collection_name)
        return collection_name
    except Exception:
        raise FileNotFoundError(f"Knowledge base collection '{collection_name}' for key '{c_key}' not found in QDrant.")

# Formátování textových bloků pro kontext do GPT
def format_context(chunks):
    if not chunks: return ""
    return "\n\n".join([f"Heading: {c['heading']}\n{c['text']}" for c in chunks])

# Reranking pomocí transformer modelu podle relevance k dotazu
async def rerank(query, candidates, top_n=1): 
    if not candidates:
        return []

    query_emb = colbert_model.encode([query], is_query=True)
    headings = [c['heading'] for c in candidates]
    texts = [c['text'] for c in candidates]
    candidate_ids = list(range(len(candidates)))

    
    h_embs = [colbert_model.encode(headings, is_query=False)]
    t_embs = [colbert_model.encode(texts, is_query=False)]

    h_reranked = rank.rerank(
        documents_ids=[candidate_ids],
        queries_embeddings=query_emb,
        documents_embeddings=h_embs
    )

    t_reranked = rank.rerank(
        documents_ids=[candidate_ids],
        queries_embeddings=query_emb,
        documents_embeddings=t_embs
    )

    results = []
    
    if h_reranked and h_reranked[0]:
        best_h_idx = h_reranked[0][0]['id']
        results.append(candidates[best_h_idx])

    
    if t_reranked and t_reranked[0]:
        best_t_idx = t_reranked[0][0]['id']
        winner_by_text = candidates[best_t_idx]
        
        if not any(c['text'] == winner_by_text['text'] and 
                   c['heading'] == winner_by_text['heading'] for c in results):
            results.append(winner_by_text)

    return results


async def retrieve_context(query, collection_name, top_k=10, min_similarity=0.8):
    qdrant_client = await get_qdrant_client() # Zajištění, že klient je inicializován
    
    #Normalizace
    query_vec = embed_model.encode([query])
    query_vec = query_vec / np.linalg.norm(query_vec, axis=1, keepdims=True)

    
    search_results = await qdrant_client.query_points( 
        collection_name=collection_name,
        query=query_vec[0].tolist(),
        limit=top_k,
        search_params=SearchParams(exact=False),
        query_filter=qmodels.Filter(
        must_not=[
            qmodels.HasIdCondition(has_id=[0])
        ]
    )
    )


    # Kontrola, zda je pole výsledků prázdné
    
    if not search_results.points:
        logger.info("No relevant context found.")
        return []

    
    max_sim = search_results.points[0].score 
    
    if max_sim < min_similarity:
        logger.info(f"Query not related (cosine similarity = {max_sim:.2f}). No context used.")
        return []

    logger.info(f"Relevant query (cosine similarity = {max_sim:.2f}) -> using context.")
    
    
    retrieved_chunks = [hit.payload for hit in search_results.points if hit.score >= min_similarity] 
    logger.info("returning chunks")
    return retrieved_chunks

async def retrieve_subjectList(collection_name):
    qdrant_client = await get_qdrant_client()
    subject_list_result = await qdrant_client.retrieve( 
        collection_name=collection_name,
        ids=[0],
        with_payload=True,
        with_vectors=False  
    )

   
    if not subject_list_result:
        return None 

    return subject_list_result[0].payload

# Debug vypisu bloku
def print_context(chunks):
    if not chunks:
        logger.info("No context chunks used.")
        return
        
    logger.info(f"--- Using {len(chunks)} unique context chunk(s) ---")
    for i, c in enumerate(chunks, 1):
        logger.info(f"Chunk {i} | Heading: {c['heading']}")
        snippet = c['text'][:150].replace('\n', ' ')
        logger.info(f"Snippet: {snippet}...")
    logger.info("------------------------------------------")


async def ask_rag(query, c_key, chat_history=None):
    logger.info(f"Loading knowledge base for: {c_key}")
    try:
        collection_name = await check_c_exists(c_key) 
        ansType = "ai"
    except FileNotFoundError as e:
        ansType = "error"
        return f"Zvolená znalostní báze nebyla nalezena: {e}"

    candidates = await retrieve_context(query, collection_name)
    context_text = ""

    if candidates:
        top_chunks = await rerank(query, candidates, top_n=1) 
        print_context(top_chunks)
        context_text = format_context(top_chunks)

    if chat_history is None:
        chat_history = []


    memory = chat_history[-10:]  # Paměť omezena na posledních 10 zpráv (5 výměn)


    # Sestavení zpráv pro model
    obor_label = collection_name

    messages = [
        {
        "role": "system",
        "content": (
            f"Jsi informovaný asistent pro školu SPŠE Plzeň, obor: {obor_label}.\n"
            "Tvé odpovědi musí vycházet VÝHRADNĚ z poskytnutých dat. Pokud informace v datech není, přiznej to.\n"
            "Pravidla:\n"
            "- Používej HTML seznamy (ul/li).\n"
            "- Odpovídej přátelsky s emoji.\n"
            "- Pokud otázka nesouvisí s oborem nebo školou, slušně odmítni odpověď."
        )
    }
    ]

    subject_list = await retrieve_subjectList(collection_name)
    subject_text = subject_list.get('text', '') if subject_list else "Seznam předmětů není dostupný."

# Vytvoříme jeden ucelený blok informací
    knowledge_block = f"SEZNAM PŘEDMĚTŮ OBORU:\n{subject_text}\n\n"
    if context_text:
        knowledge_block += f"SPECIFICKÉ INFORMACE K DOTAZU:\n{context_text}"

# Přidáme data jako systémový kontext nebo uživatelský kontext
    messages.append({
        "role": "system",
        "content": (
           "ZDE JSOU TVÉ ZNALOSTI (Znalostní báze):\n"
          "====================================\n"
         f"{knowledge_block}\n"
         "====================================\n"
        "INSTRUKCE PRO PŘÍPAD CHYBĚJÍCÍCH DAT:\n"
        "Pokud odpověď na otázku není v těchto datech obsažena, neodpovídej obecně. "
        "Místo toho slušně požádej uživatele, aby svou otázku upřesnil – například aby "
        "uvedl konkrétní název předmětu, na který se ptá (pokud ho v otázce nezmínil)."
        )
    })

    # Přidání předchozí konverzace do zpráv
    for turn in memory:
        messages.append({"role": "user", "content": turn["user"]})
        messages.append({"role": "assistant", "content": turn["ai"]})

    messages.append({"role": "user", "content": query})

    # Odeslání dotazu
    response = await client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        temperature=0.3,
        max_tokens=600
    )

    answer = response.choices[0].message.content.strip()

    # Výpis počtu tokenů
    input_tokens = sum(count_tokens(m["content"]) for m in messages)
    output_tokens = count_tokens(answer)
    logger.info(f"\nTokens — Prompt: {input_tokens}, Completion: {output_tokens}, Total: {input_tokens + output_tokens}")
    return {
        "answer": answer,
        "ansType": ansType
    }

# FastAPI
async def run_query(query: str, c_key: str, chat_history: list = None) -> dict:
    return await ask_rag(query, c_key, chat_history)