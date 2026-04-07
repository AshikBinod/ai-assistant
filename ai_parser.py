import requests
import os
import json
import re

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def parse_command(user_input):
    # 🔥 Improved prompt for better titles
    prompt = f"""
    Convert this into STRICT JSON ONLY.

    Extract a SHORT task title (1–3 words max).

    Examples:
    - "remind me to study at 10 pm" → "Study"
    - "check on my workout in 30 minutes" → "Workout"

    Input:
    "{user_input}"

    Output format:
    {{
        "title": "...",
        "time": "YYYY-MM-DDTHH:MM:SS"
    }}

    No explanation. No markdown. Only JSON.
    """

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        )

        result = response.json()
        print("DEBUG RESPONSE:", result)

        # 🔥 Handle API error properly
        if "error" in result:
            raise ValueError(result["error"]["message"])

        content = result["choices"][0]["message"]["content"]

        print("RAW OUTPUT:", content)

        # 🔥 Remove markdown if present
        content = content.replace("```json", "").replace("```", "").strip()

        # 🔥 Extract JSON safely
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