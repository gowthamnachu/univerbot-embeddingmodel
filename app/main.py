"""
UniverBot Embedding Service

Standalone microservice for generating text embeddings using sentence-transformers.
Uses all-MiniLM-L6-v2 model (384 dimensions, ~100MB, ~25ms per embedding).
"""

import os
from typing import List
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Initialize FastAPI app
app = FastAPI(
    title="UniverBot Embedding Service",
    description="Generate text embeddings using sentence-transformers",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model configuration
MODEL_NAME = "all-MiniLM-L6-v2"
MODEL_DIMENSION = 384
MAX_BATCH_SIZE = 100


# Pydantic models for request/response
class EmbedRequest(BaseModel):
    text: str = Field(..., description="Text to generate embedding for")


class EmbedResponse(BaseModel):
    embedding: List[float]
    dimension: int
    model: str


class BatchEmbedRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to generate embeddings for", max_length=MAX_BATCH_SIZE)


class BatchEmbedResponse(BaseModel):
    embeddings: List[List[float]]
    dimension: int
    model: str
    count: int


class HealthResponse(BaseModel):
    status: str
    model: str
    dimension: int
    ready: bool


# Lazy load the model to avoid startup delays
@lru_cache(maxsize=1)
def get_model():
    """Load and cache the sentence transformer model."""
    print(f"🔄 Loading embedding model: {MODEL_NAME}...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_NAME)
    print(f"✅ Model loaded successfully. Dimension: {model.get_sentence_embedding_dimension()}")
    return model


@app.on_event("startup")
async def startup_event():
    """Pre-load the model on startup."""
    print("🚀 Starting UniverBot Embedding Service...")
    try:
        get_model()
        print("✅ Service ready to accept requests")
    except Exception as e:
        print(f"⚠️ Warning: Could not pre-load model: {e}")
        print("   Model will be loaded on first request")


@app.get("/", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        model = get_model()
        return HealthResponse(
            status="healthy",
            model=MODEL_NAME,
            dimension=MODEL_DIMENSION,
            ready=True
        )
    except Exception as e:
        return HealthResponse(
            status=f"unhealthy: {str(e)}",
            model=MODEL_NAME,
            dimension=MODEL_DIMENSION,
            ready=False
        )


@app.post("/embed", response_model=EmbedResponse)
async def generate_embedding(request: EmbedRequest):
    """Generate embedding for a single text."""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        model = get_model()
        embedding = model.encode(request.text, convert_to_numpy=True)
        
        return EmbedResponse(
            embedding=embedding.tolist(),
            dimension=MODEL_DIMENSION,
            model=MODEL_NAME
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embedding: {str(e)}")


@app.post("/embed/batch", response_model=BatchEmbedResponse)
async def generate_batch_embeddings(request: BatchEmbedRequest):
    """Generate embeddings for multiple texts in batch."""
    try:
        if not request.texts:
            raise HTTPException(status_code=400, detail="Texts list cannot be empty")
        
        if len(request.texts) > MAX_BATCH_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"Maximum batch size is {MAX_BATCH_SIZE}, got {len(request.texts)}"
            )
        
        # Filter out empty texts
        valid_texts = [t for t in request.texts if t.strip()]
        if not valid_texts:
            raise HTTPException(status_code=400, detail="All texts are empty")
        
        model = get_model()
        embeddings = model.encode(valid_texts, convert_to_numpy=True)
        
        return BatchEmbedResponse(
            embeddings=[emb.tolist() for emb in embeddings],
            dimension=MODEL_DIMENSION,
            model=MODEL_NAME,
            count=len(valid_texts)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    print(f"🌐 Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
