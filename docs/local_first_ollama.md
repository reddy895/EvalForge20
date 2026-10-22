# Local-First Ollama Evaluation Guide

## Zero Cloud Key Guarantee
EvalForge20 requires **zero cloud API credentials** to start, discover models, and run comprehensive evaluations.

### Quick Start
1. Install Ollama:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```
2. Pull recommended evaluation models:
   ```bash
   ollama pull qwen2.5:7b
   ollama pull llama3.1:8b
   ```
3. Start EvalForge20:
   ```bash
   ./scripts/run_dev.sh
   ```
The platform automatically detects local models and configures them for immediate evaluation.
