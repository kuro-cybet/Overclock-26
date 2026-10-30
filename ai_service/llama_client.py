import logging
import httpx
from typing import List, Dict, Any, Optional
from ai_service.config import config

logger = logging.getLogger("ai_service.llama_client")

class LlamaCppClient:
    def __init__(self):
        self.base_url = config.LLAMA_CPP_BASE_URL.rstrip("/")
        self.model = config.LLAMA_CPP_MODEL
        self.timeout = config.INFERENCE_TIMEOUT

    async def check_health(self) -> bool:
        """Checks if llama.cpp server is reachable and active."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/models")
                return res.status_code == 200
        except Exception as e:
            logger.warning(f"llama.cpp health check failed: {e}")
            return False

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 800,
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        """Calls the OpenAI-compatible /v1/chat/completions endpoint on llama.cpp."""
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                res = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload
                )
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]
            except httpx.ConnectError as ce:
                logger.error(f"Cannot connect to llama.cpp server at {self.base_url}: {ce}")
                raise RuntimeError(f"llama.cpp server connection failed at {self.base_url}")
            except httpx.TimeoutException:
                logger.error(f"llama.cpp inference timed out after {self.timeout}s")
                raise TimeoutError(f"llama.cpp inference timed out after {self.timeout}s")
            except Exception as e:
                logger.error(f"llama.cpp chat completion error: {e}")
                raise

llama_client = LlamaCppClient()

