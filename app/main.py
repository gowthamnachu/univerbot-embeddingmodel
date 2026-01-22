from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from sentence_transformers import SentenceTransformer
from functools import lru_cache
import os
import asyncio

app = FastAPI(
    title="UniverBot Embedding Service",
    version="1.0.0"
)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MAX_TEXT_LENGTH = 5000
MAX_BATCH_SIZE = 100


@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer(EMBEDDING_MODEL)


@app.on_event("startup")
def preload_model():
    get_model()  # single, controlled load


class EmbeddingRequest(BaseModel):
    text: str = Field(..., max_length=MAX_TEXT_LENGTH)


class EmbeddingBatchRequest(BaseModel):
    texts: List[str] = Field(..., max_items=MAX_BATCH_SIZE)


class EmbeddingResponse(BaseModel):
    embedding: List[float]
    dimension: int
    model: str


class EmbeddingBatchResponse(BaseModel):
    embeddings: List[List[float]]
    dimension: int
    model: str
    count: int


@app.get("/health")
def health():
    model = get_model()
    return {
        "status": "healthy",
        "model": EMBEDDING_MODEL,
        "dimension": model.get_sentence_embedding_dimension()
    }


async def encode_async(texts):
    loop = asyncio.get_running_loop()
    model = get_model()
    return await loop.run_in_executor(
        None,
        lambda: model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )
    )


@app.post("/embed", response_model=EmbeddingResponse)
async def embed(request: EmbeddingRequest):
    embedding = await encode_async(request.text)

    return EmbeddingResponse(
        embedding=embedding.tolist(),
        dimension=len(embedding),
        model=EMBEDDING_MODEL
    )


@app.post("/embed/batch", response_model=EmbeddingBatchResponse)
async def embed_batch(request: EmbeddingBatchRequest):
    if not request.texts:
        raise HTTPException(status_code=400, detail="No texts provided")

    embeddings = await encode_async(request.texts)

    return EmbeddingBatchResponse(
        embeddings=[e.tolist() for e in embeddings],
        dimension=embeddings.shape[1],
        model=EMBEDDING_MODEL,
        count=len(embeddings)
    )
