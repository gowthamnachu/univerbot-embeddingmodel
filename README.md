# UniverBot Embedding Service

Standalone microservice for generating text embeddings using sentence-transformers.

## Features

- 🚀 **Fast**: Uses all-MiniLM-L6-v2 (100MB model, 25ms per embedding)
- 📊 **384 Dimensions**: Optimized for storage and speed
- 🔄 **Batch Processing**: Process up to 100 texts in one request
- 💾 **Memory Efficient**: ~150MB RAM total (fits 512MB free tier)
- 🐳 **Docker Ready**: Pre-built container with model included

## Model Specifications

- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Size**: ~100MB
- **Speed**: ~25ms per embedding
- **Quality**: 65.2% on SBERT benchmark

## API Endpoints

### Health Check

```bash
GET /
GET /health
```

### Single Embedding

```bash
POST /embed
Content-Type: application/json

{
  "text": "Your text here"
}
```

**Response:**

```json
{
  "embedding": [0.123, -0.456, ...],
  "dimension": 384,
  "model": "all-MiniLM-L6-v2"
}
```

### Batch Embeddings

```bash
POST /embed/batch
Content-Type: application/json

{
  "texts": ["Text 1", "Text 2", "Text 3"]
}
```

**Response:**

```json
{
  "embeddings": [[...], [...], [...]],
  "dimension": 384,
  "model": "all-MiniLM-L6-v2",
  "count": 3
}
```

## Local Development

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Service

```bash
python -m app.main
# or
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 3. Test the Service

```bash
# Health check
curl http://localhost:8001/health

# Generate embedding
curl -X POST http://localhost:8001/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}'
```

## Docker Deployment

### Build Image

```bash
docker build -t univerbot-embedding:latest .
```

### Run Container

```bash
docker run -p 8001:8001 univerbot-embedding:latest
```

## Cloud Deployment

### Koyeb (Recommended - Free 512MB)

1. Push to GitHub
2. Connect Koyeb to your repo
3. Select `univerbot-embeddingmodel` as root directory
4. Set build command: `docker build -t embedding .`
5. Set port: `8001`
6. Deploy!

**Estimated RAM**: ~150MB (fits comfortably in 512MB)

### Fly.io

```bash
fly launch --dockerfile Dockerfile
fly deploy
```

### Render

1. Create new "Web Service"
2. Connect repo
3. Set root directory: `univerbot-embeddingmodel`
4. Docker deployment
5. Deploy

### Railway

```bash
railway init
railway up
```

## Integration with Main Backend

Update your main backend's `embeddings.py` to call this service:

```python
import httpx

EMBEDDING_SERVICE_URL = "http://your-embedding-service.koyeb.app"

async def generate_embeddings(text: str) -> List[float]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{EMBEDDING_SERVICE_URL}/embed",
            json={"text": text}
        )
        response.raise_for_status()
        return response.json()["embedding"]

async def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{EMBEDDING_SERVICE_URL}/embed/batch",
            json={"texts": texts}
        )
        response.raise_for_status()
        return response.json()["embeddings"]
```

Add to main backend requirements:

```
httpx>=0.25.0
```

## Environment Variables

- `PORT`: Server port (default: 8001)
- `PYTHONUNBUFFERED`: Set to 1 for better logging

## Resource Requirements

| Platform              | RAM   | Works?   |
| --------------------- | ----- | -------- |
| Koyeb Free            | 512MB | ✅ Yes   |
| Render Free           | 512MB | ✅ Yes   |
| Fly.io Free           | 256MB | ⚠️ Tight |
| Railway Free          | 512MB | ✅ Yes   |
| Google Cloud e2-micro | 1GB   | ✅ Yes   |

## Performance

- **Cold Start**: ~2-3 seconds (model pre-loaded in Docker)
- **Single Embedding**: ~25ms
- **Batch (10 texts)**: ~100ms
- **Concurrent Requests**: Handles 10+ simultaneous requests

## License

MIT
