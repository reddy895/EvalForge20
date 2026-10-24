# Local-First Ollama Evaluation Guide & Troubleshooting

EvalForge20 is designed ground-up for **100% private, local-first evaluation** using Ollama without requiring cloud API keys or external telemetry servers.

---

## 1. Quick Setup

### Step 1: Install Ollama

- **Linux**:
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```
- **macOS**:
  Download from [ollama.com/download](https://ollama.com/download) or run:
  ```bash
  brew install ollama
  ```
- **Windows**:
  Download and run the installer from [ollama.com/download](https://ollama.com/download).

### Step 2: Verify Ollama Service

Ensure the daemon is listening on port `11434`:
```bash
curl -s http://127.0.0.1:11434/api/version
# Output: {"version":"0.5.x"}
```

### Step 3: Pull Evaluation Models

For fast local testing and benchmarking, pull at least two distinct models:

```bash
# Lightweight models (fastest inference, low RAM usage)
ollama pull qwen2.5:1.5b
ollama pull llama3.2:1b

# Standard benchmark models (higher accuracy, 8GB+ RAM recommended)
ollama pull qwen2.5:7b
ollama pull mistral:7b
```

Verify installed models:
```bash
ollama list
```

---

## 2. Running EvalForge20

### Start Backend and Frontend

```bash
# Option A: One-command launch script
./scripts/run_dev.sh

# Option B: Manual services
# Terminal 1: Backend
cd backend && uv run uvicorn src.evalforge.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

The frontend will be accessible at `http://localhost:5173`, with the backend API at `http://localhost:8000`.

---

## 3. Running Multi-Model Evaluations

1. Open the **Evaluate** page in the dashboard.
2. Select target models (e.g. `qwen2.5:1.5b` and `llama3.2:1b`).
3. Select an evaluation dataset (e.g., `Python Algorithmic Synthesis` or `Constrained JSON Schema Extraction`).
4. Click **Run Evaluation**.
5. Observe live test-case results, individual outputs, tokens/sec, and real-time pass-rate updates.
6. Open the **Analytics** or **Compare** pages to inspect side-by-side empirical performance.

---

## 4. Troubleshooting Common Failures

### 1. Connection Refused (`127.0.0.1:11434`)
- **Symptom**: Health badge shows `Ollama Disconnected`, requests fail with `connection_error`.
- **Cause**: Ollama daemon is not running or listening on a different host interface.
- **Fix**:
  ```bash
  # Check if process is running
  pgrep -l ollama
  # Start daemon if stopped
  ollama serve
  ```
  If running inside Docker, ensure `OLLAMA_BASE_URL=http://host.docker.internal:11434` or set `OLLAMA_HOST=0.0.0.0:11434`.

### 2. Model Not Found (404)
- **Symptom**: Error message contains `model 'xxx' not found, try pulling it first`.
- **Cause**: Model tag differs between catalog and local installation.
- **Fix**:
  Pull the exact tag reported:
  ```bash
  ollama pull qwen2.5:1.5b
  ```
  EvalForge20 automatically normalizes tags (e.g., stripping `:latest` when matching base names).

### 3. VRAM Out-of-Memory (OOM) or Extreme Latency
- **Symptom**: Model takes > 60s to load, system freezes or drops throughput.
- **Cause**: Model size exceeds GPU VRAM and falls back to CPU RAM swapping.
- **Fix**:
  Use smaller quantized versions or parameter sizes (e.g., `qwen2.5:1.5b` or `llama3.2:1b` which require only ~2 GB RAM).

### 4. Read Timeout During Long Prompts
- **Symptom**: `Ollama request timed out after 30s` error recorded in reliability metrics.
- **Cause**: Large context window processing exceeding default timeout.
- **Fix**:
  Configure timeout in `.env`:
  ```bash
  OLLAMA_TIMEOUT_SECONDS=120
  ```

---

## 5. Running Automated Tests

```bash
# Run all unit tests (isolated with deterministic mocks, no Ollama required)
cd backend && uv run pytest -v

# Run multi-model regression suite
cd backend && uv run pytest tests/test_model_cross_contamination.py -v

# Run frontend tests
cd frontend && npm test -- --run
```
