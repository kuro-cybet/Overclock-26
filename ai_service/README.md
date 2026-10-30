# CampusOps Local Qwen AI Microservice (llama.cpp)

This dedicated microservice bridges the **Meta WhatsApp Cloud API / CampusOps Backend** running on Render with the local **Qwen GGUF model** running on **llama.cpp**.

---

## 1. Prerequisites

1. **llama.cpp server** running locally with a Qwen GGUF model:
   ```bash
   llama-server.exe -m path/to/qwen-7b-chat.Q4_K_M.gguf --port 8080 --host 127.0.0.1 -c 4096 --alias qwen-local
   ```
2. **Python 3.11** environment.
3. **ngrok** tunnel (to expose the local microservice to the Render backend).

---

## 2. Configuration (`.env`)

Create or update `.env` in `ai_service/`:

```env
LLAMA_CPP_BASE_URL=http://127.0.0.1:8080/v1
LLAMA_CPP_MODEL=qwen-local
AI_SERVICE_TOKEN=campusops_ai_secret_token_2026
AI_SERVICE_PORT=8001
INFERENCE_TIMEOUT=60.0
```

---

## 3. Starting the AI Microservice

```powershell
python -m uvicorn ai_service.main:app --host 0.0.0.0 --port 8001 --reload
```

Test health:
```powershell
curl http://localhost:8001/health
```

---

## 4. Exposing via ngrok

```bash
ngrok http 8001
```

Copy the generated HTTPS URL (e.g. `https://xyz.ngrok-free.app`) and configure it on the CampusOps Render backend:
```env
AI_SERVICE_URL=https://xyz.ngrok-free.app
AI_SERVICE_TOKEN=campusops_ai_secret_token_2026
```

