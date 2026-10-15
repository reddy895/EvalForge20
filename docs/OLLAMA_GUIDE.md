# Local-First Ollama Workflow Guide

EvalForge20 provides native, independent local LLM evaluation powered by Ollama without requiring external cloud accounts or paid API keys.

---

## 1. Quick Setup

### Install Ollama
- **Linux/macOS:**
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```
- **Windows:** Download from [ollama.com/download](https://ollama.com/download).

### Launch the Daemon
Ensure the local Ollama server is running:
```bash
ollama serve
```
By default, the server listens at `http://localhost:11434`.

### Pull Local Models
Download your desired evaluation model(s):
```bash
ollama pull qwen2.5:3b
ollama pull llama3.2:1b
```

---

## 2. Model Discovery and Verification

### Using CLI
List all installed models and their quantization levels:
```bash
python -m evalforge models
# or
evalforge20 models
```

Verify whether a specific model is ready for evaluation:
```bash
python -m evalforge models check qwen2.5:3b
```

### Using REST API
Query local daemon health and installed models:
```bash
# Diagnostic report
curl http://localhost:8000/v1/ollama/status

# Detailed model metadata
curl http://localhost:8000/v1/models
```

---

## 3. Running an Evaluation

Execute evaluation using the CLI against any local dataset:
```bash
python -m evalforge evaluate \
  --dataset examples/datasets/qa_sample.json \
  --provider ollama \
  --model qwen2.5:3b \
  --metrics exact_match,token_f1,response_completeness
```

### Configuration Options
The Ollama provider supports fine-grained inference parameters via environment variables or options:
- `OLLAMA_BASE_URL`: Endpoint (default: `http://localhost:11434`)
- `OLLAMA_MODEL`: Default model (default: `qwen2.5:3b`)
- `OLLAMA_TEMPERATURE`: Sampling temperature (default: `0.7`)
- `OLLAMA_CONTEXT_LENGTH`: Context window size (default: `4096`)
- `OLLAMA_TIMEOUT_SECONDS`: Request timeout (default: `120.0`)

---

## 4. Comparing Models

Compare two evaluation runs on the same dataset to measure quality and latency differences:
```bash
python -m evalforge compare RUN_ID_BASELINE RUN_ID_CANDIDATE
```

Generate multi-run comparison matrix via API:
```bash
curl -X POST http://localhost:8000/v1/compare/matrix \
  -H "Content-Type: application/json" \
  -d '{"run_ids": ["RUN_ID_1", "RUN_ID_2"]}'
```

---

## 5. Exporting Reports

Export results in Markdown, CSV, or JSON:
```bash
# Markdown report
python -m evalforge report export RUN_ID --format markdown --output reports/run.md

# CSV per-case results
python -m evalforge report export RUN_ID --format csv --output reports/cases.csv

# JSON complete schema
python -m evalforge report export RUN_ID --format json --output reports/run.json
```
