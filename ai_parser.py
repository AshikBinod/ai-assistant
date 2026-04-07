import requests
import os
import json

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def parse_command(user_input):
    prompt = f"""
    Convert this into STRICT JSON:

    "{user_input}"

    Format:
    {{
        "title": "...",
        "time": "YYYY-MM-DDTHH:MM:SS"
    }}

    Only return JSON.
    """

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )

    result = response.json()
    content = result["choices"][0]["message"]["content"]

    try:
        return json.loads(content)
    except:
        return {
            "title": "Fallback Task",
            "time": "2026-04-07T22:00:00"
        }