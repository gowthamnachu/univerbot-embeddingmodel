# Deployment Troubleshooting Guide

## Common Deployment Errors & Solutions

### 1. Health Check Failures

**Symptoms:**

- "Application failed health checks"
- "Service unhealthy"
- Deployment times out

**Solutions:**

✅ **Check 1: Model Loading Time**
The model takes ~10-15 seconds to download and load on first run. Increase health check timeouts:

```yaml
# For Fly.io (fly.toml)
[[http_service.checks]]
  grace_period = "30s"  # Wait 30s before first check
  timeout = "10s"
```

```yaml
# For Render (render.yaml)
healthCheckPath: /health
initialDelaySeconds: 30
```

✅ **Check 2: Test Locally**

```bash
cd univerbot-embeddingmodel
docker build -t test-embed .
docker run -p 8001:8001 test-embed

# In another terminal
curl http://localhost:8001/health
```

Should return:

```json
{
  "status": "healthy",
  "model": "all-MiniLM-L6-v2",
  "dimension": 384,
  "ready": true
}
```

---

### 2. Memory Issues (OOM - Out of Memory)

**Symptoms:**

- "Killed" in logs
- "OOMKilled" error
- Deployment crashes after starting

**Solutions:**

✅ **Minimum RAM Required:** 180-200MB

| Platform | Free Tier RAM | Works?   | Fix               |
| -------- | ------------- | -------- | ----------------- |
| Fly.io   | 256MB         | ⚠️ Tight | Increase to 512MB |
| Koyeb    | 512MB         | ✅ Yes   | Default OK        |
| Render   | 512MB         | ✅ Yes   | Default OK        |
| Railway  | 512MB         | ✅ Yes   | Default OK        |

**For Fly.io - Upgrade Memory:**

```bash
fly scale memory 512
```

Or update `fly.toml`:

```toml
[[vm]]
  memory = '512mb'  # Changed from 256mb
  cpu_kind = 'shared'
  cpus = 1
```

---

### 3. Port Binding Issues

**Symptoms:**

- "Address already in use"
- "Failed to bind to port"
- Works locally but not deployed

**Solutions:**

✅ **Use Dynamic PORT Variable**

The fixed Dockerfile now uses `$PORT` environment variable:

```dockerfile
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}
```

✅ **Platform-Specific Checks:**

**Render:**

- Automatically provides `PORT` environment variable
- No action needed

**Fly.io:**

- Uses `internal_port = 8001` in fly.toml
- Automatically maps to public URL

**Koyeb:**

- Set "Exposed Port" to `8001` in dashboard
- Enable "Public" exposure

---

### 4. Build Failures

**Symptoms:**

- "Failed to build Docker image"
- "No such file or directory"
- "requirements.txt not found"

**Solutions:**

✅ **Check File Structure:**

```
univerbot-embeddingmodel/
├── Dockerfile          ✅ Must be here
├── requirements.txt    ✅ Must be here
├── Procfile           ✅ Must be here
└── app/
    ├── __init__.py    ✅ Must be here
    └── main.py        ✅ Must be here
```

✅ **Verify Build Context:**

```bash
# Test build locally
cd univerbot-embeddingmodel
docker build -t test .
```

---

### 5. Model Download Failures

**Symptoms:**

- "Connection timeout during model download"
- "HuggingFace hub unreachable"
- "Failed to load model"

**Solutions:**

✅ **Pre-download in Dockerfile (Already Done)**

```dockerfile
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

✅ **Check Outbound Network Access:**
Some platforms block outbound connections during build. If model download fails:

**Option 1: Use Larger Base Image**

```dockerfile
FROM python:3.11  # Instead of python:3.11-slim
```

**Option 2: Manual Model Files**
Download model locally and include in build (not recommended - increases image size).

---

## Platform-Specific Deployment Instructions

### 🚀 Koyeb (Recommended - Most Reliable)

1. **Push to GitHub:**

   ```bash
   cd univerbot-embeddingmodel
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Koyeb:**
   - Go to https://app.koyeb.com
   - Click "Create App"
   - Select "GitHub" as source
   - Choose your repo
   - **Builder:** Docker
   - **Dockerfile path:** `Dockerfile`
   - **Port:** `8001`
   - **Instance:** Nano (512MB) - Free
   - **Health Check Path:** `/health`
   - **Initial Delay:** `30 seconds`
   - Deploy!

3. **Test:**
   ```bash
   curl https://your-app.koyeb.app/health
   ```

---

### ✈️ Fly.io

1. **Install Fly CLI:**

   ```bash
   # Windows
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **Login & Deploy:**

   ```bash
   cd univerbot-embeddingmodel
   fly auth login
   fly launch  # Use existing fly.toml
   fly deploy
   ```

3. **If Memory Issues:**

   ```bash
   fly scale memory 512
   fly deploy
   ```

4. **Check Status:**
   ```bash
   fly status
   fly logs
   ```

---

### 🎨 Render

1. **Connect Repository:**
   - Go to https://render.com
   - New → Web Service
   - Connect GitHub repo

2. **Configuration:**
   - **Environment:** Docker
   - **Region:** Choose closest
   - **Instance Type:** Free (512MB)
   - **Health Check Path:** `/health`
   - **Health Check Timeout:** `30` seconds
   - Deploy!

3. **Update render.yaml (if needed):**
   ```yaml
   services:
     - type: web
       name: univerbot-embedding
       env: docker
       plan: free
       healthCheckPath: /health
       initialDelaySeconds: 30
   ```

---

### 🚂 Railway

1. **Create Project:**

   ```bash
   npm i -g @railway/cli
   railway login
   cd univerbot-embeddingmodel
   railway init
   railway up
   ```

2. **Configure:**
   - Environment Variables: None needed (uses defaults)
   - Port: Automatically detected
   - Health Check: Automatic

---

## Quick Diagnostics

### Test 1: Local Docker

```bash
cd univerbot-embeddingmodel
docker build -t embed-test .
docker run -p 8001:8001 embed-test

# Should see:
# 🚀 Starting UniverBot Embedding Service...
# 🔄 Loading embedding model: all-MiniLM-L6-v2
# ✅ Model loaded. Dimension: 384
# ✅ Service ready!
```

### Test 2: Health Check

```bash
curl http://localhost:8001/health
# Expected: {"status":"healthy","model":"all-MiniLM-L6-v2","dimension":384,"ready":true}
```

### Test 3: Generate Embedding

```bash
curl -X POST http://localhost:8001/embed \
  -H "Content-Type: application/json" \
  -d '{"text":"hello world"}'

# Should return 384-dimensional vector
```

### Test 4: Memory Usage

```bash
docker stats

# Should show ~150-180MB RAM usage
```

---

## Logs Analysis

### ✅ Healthy Logs Look Like:

```
INFO:     Started server process
INFO:     Waiting for application startup.
🚀 Starting UniverBot Embedding Service...
🔄 Loading embedding model: all-MiniLM-L6-v2
✅ Model loaded. Dimension: 384
✅ Service ready!
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### ❌ Problem Logs:

**Memory Issue:**

```
Killed
OOMKilled
137 exit code
```

**Fix:** Increase RAM to 512MB

**Port Issue:**

```
Address already in use
Cannot bind to port
```

**Fix:** Use PORT environment variable (already fixed in Dockerfile)

**Model Download Issue:**

```
ConnectionError: HuggingFace Hub
Timeout during model download
```

**Fix:** Check outbound network access, may need to change platform

**Health Check Timeout:**

```
Failed health check
Service unhealthy after 3 attempts
```

**Fix:** Increase grace period to 30-40 seconds

---

## Still Having Issues?

1. **Share deployment logs** - Copy full logs from platform
2. **Test locally first** - Run `docker build` and `docker run`
3. **Check platform status** - Sometimes platforms have outages
4. **Try different platform** - Koyeb tends to be most reliable

## Post-Deployment

Once deployed successfully:

1. **Get your service URL** (e.g., `https://your-app.koyeb.app`)

2. **Update main backend `.env`:**

   ```env
   EMBEDDING_SERVICE_URL=https://your-app.koyeb.app
   EMBEDDING_PROVIDER=microservice
   ```

3. **Test integration:**

   ```bash
   curl -X POST https://your-app.koyeb.app/embed \
     -H "Content-Type: application/json" \
     -d '{"text":"test"}'
   ```

4. **Monitor health:**
   ```bash
   curl https://your-app.koyeb.app/health
   ```

---

## Performance Tuning

### Cold Start Optimization

Model is pre-loaded in Docker image, so cold starts are ~2-3 seconds.

### Auto-scaling

- **Fly.io:** `min_machines_running = 0` (scales to zero)
- **Render:** Always-on on free tier
- **Koyeb:** Always-on on free tier

### Request Optimization

Use batch endpoint for multiple texts:

```bash
curl -X POST /embed/batch \
  -d '{"texts":["text1","text2","text3"]}'
```
