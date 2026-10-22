# Provider Integration Matrix

EvalForge20 provides unified inference interfaces for 15 providers:

1. **Ollama**: Default local provider (`http://localhost:11434`)
2. **Mock**: Deterministic offline provider for hermetic testing
3. **OpenAI-Compatible**: Generic REST adapter for vLLM, LMStudio, LocalAI
4. **OpenAI**: Frontier cloud provider (`OPENAI_API_KEY`)
5. **Anthropic**: Claude Messages API (`ANTHROPIC_API_KEY`)
6. **Google Gemini**: Gemini Developer API (`GEMINI_API_KEY`)
7. **Groq**: Ultra-low latency LPU inference (`GROQ_API_KEY`)
8. **Mistral AI**: European frontier models (`MISTRAL_API_KEY`)
9. **Cohere**: Enterprise RAG & Command models (`COHERE_API_KEY`)
10. **Together AI**: Open-weights cloud endpoints (`TOGETHER_API_KEY`)
11. **Fireworks AI**: High-throughput inference (`FIREWORKS_API_KEY`)
12. **DeepSeek**: Code and reasoning models (`DEEPSEEK_API_KEY`)
13. **Hugging Face**: Serverless Inference API (`HUGGINGFACE_API_KEY`)
14. **Azure OpenAI**: Enterprise cloud deployment (`AZURE_OPENAI_API_KEY`)
15. **AWS Bedrock**: AWS managed foundation models (`AWS_ACCESS_KEY_ID`)
