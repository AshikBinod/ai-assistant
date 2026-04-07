import requests
import os
import json
import re
from datetime import datetime, timedelta

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def parse_command(user_input):
    # 🔥 Simple prompt (ONLY title)
    prompt = f"""
    Extract a SHORT task title (1–3 words).

    Input:
    "{user_input}"

    Output JSON:
    {{
        "title": "..."
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
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        )

        result = response.json()
        print("DEBUG RESPONSE:", result)

        content = result["choices"][0]["message"]["content"]
        content = content.replace("```json", "").replace("```", "").strip()

        match = re.search(r"\{.*\}", content, re.DOTALL)
        data = json.loads(match.group())

        # 🔥 TIME HANDLING (VERY IMPORTANT)
        now = datetime.now()

        if "minute" in user_input:
            minutes = int(re.search(r"\d+", user_input).group())
            scheduled_time = now + timedelta(minutes=minutes)

        elif "hour" in user_input:
            hours = int(re.search(r"\d+", user_input).group())
            scheduled_time = now + timedelta(hours=hours)

        else:
            # fallback: 1 minute later
            scheduled_time = now + timedelta(minutes=1)

        return {
            "title": data["title"],
            "time": scheduled_time.isoformat()
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "title": "Task",
            "time": (datetime.now() + timedelta(minutes=1)).isoformat()
        }