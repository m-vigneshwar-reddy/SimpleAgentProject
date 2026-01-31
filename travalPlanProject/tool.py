import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"


def estimate_budget(total_budget, days):
    return round(total_budget / days, 2)


def suggest_places(city, style):
    prompt = f"""
    Suggest exactly 3 travel activities for a {style} trip in {city}.
    Respond ONLY as a comma-separated list.
    """

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        }
    )

    data = response.json()

    # ✅ SAFE handling of Ollama response
    if "response" in data:
        text = data["response"]
    elif "message" in data and "content" in data["message"]:
        text = data["message"]["content"]
    else:
        # fallback to avoid crash
        text = "City walk, Local food tasting, Free exploration"

    return [p.strip() for p in text.split(",")][:3]
