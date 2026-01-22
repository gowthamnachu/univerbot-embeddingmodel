from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from sentence_transformers import SentenceTransformer
import uvicorn
from functools import lru_cache

app = FastAPI(title="UniverBot Embedding Service", version="1.0.0")

# Model configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Load and cache the model
@lru_cache(maxsize=1)
def get_model():
    """Load and cache the sentence transformer model."""
    print(f"🔄 Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"✅ Model loaded. Dimension: {model.get_sentence_embedding_dimension()}")
    return model


class EmbeddingRequest(BaseModel):
    text: str
    
class EmbeddingBatchRequest(BaseModel):
    texts: List[str]

class EmbeddingResponse(BaseModel):
    embedding: List[float]
    dimension: int
    model: str

class EmbeddingBatchResponse(BaseModel):
    embeddings: List[List[float]]
    dimension: int
    model: str
    count: int


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "UniverBot Embedding Service",
        "status": "running",
        "model": EMBEDDING_MODEL,
        "dimension": EMBEDDING_DIMENSION
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    try:
        model = get_model()
        return {
            "status": "healthy",
            "model": EMBEDDING_MODEL,
            "dimension": model.get_sentence_embedding_dimension(),
            "ready": True
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/embed", response_model=EmbeddingResponse)
async def create_embedding(request: EmbeddingRequest):
    """Generate embedding for a single text."""
    try:
        model = get_model()
        embedding = model.encode(request.text, convert_to_numpy=True)
        
        return EmbeddingResponse(
            embedding=embedding.tolist(),
            dimension=len(embedding),
            model=EMBEDDING_MODEL
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@app.post("/embed/batch", response_model=EmbeddingBatchResponse)
async def create_embeddings_batch(request: EmbeddingBatchRequest):
    """Generate embeddings for multiple texts (batch processing)."""
    try:
        if not request.texts:
            raise HTTPException(status_code=400, detail="No texts provided")
        
        if len(request.texts) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 texts per batch")
        
        model = get_model()
        embeddings = model.encode(request.texts, convert_to_numpy=True, show_progress_bar=False)
        
        return EmbeddingBatchResponse(
            embeddings=[emb.tolist() for emb in embeddings],
            dimension=embeddings.shape[1],
            model=EMBEDDING_MODEL,
            count=len(embeddings)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch embedding generation failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
