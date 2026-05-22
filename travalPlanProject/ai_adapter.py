import requests

from travalPlanProject.config import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS, OLLAMA_MAX_RETRIES


def call_ollama(prompt, max_retries=OLLAMA_MAX_RETRIES):
    """Call the configured Ollama endpoint and return the text response."""
    last_exception = None

    for attempt in range(max_retries):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7
                },
                timeout=OLLAMA_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            data = response.json()

            if "response" in data:
                return data["response"].strip()
            if "message" in data and "content" in data["message"]:
                return data["message"]["content"].strip()

            return None
        except Exception as exc:
            last_exception = exc
            continue

    if last_exception is not None:
        print(f"Ollama API Error after {max_retries} attempts: {last_exception}")
    return None
