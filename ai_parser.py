import requests
import os
import json
import re

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def parse_command(user_input):
    prompt = f"""
    Convert this into STRICT JSON ONLY.

    Do NOT include any explanation or text.

    "{user_input}"

    Output format:
    {{
        "title": "...",
        "time": "YYYY-MM-DDTHH:MM:SS"
    }}
    """

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        )

        result = response.json()
        print("DEBUG RESPONSE:", result)

        content = result["choices"][0]["message"]["content"]

        # 🔥 Extract only JSON from response
        match = re.search(r"\{.*\}", content, re.DOTALL)

        if match:
            return json.loads(match.group())
        else:
            raise ValueError("No JSON found")

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "title": "Fallback Task",
            "time": "2026-04-07T22:00:00"
        }