import requests
import os
import json
import re
from datetime import datetime, timedelta

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def parse_command(user_input):
    try:
        # 🔥 SIMPLE PROMPT (force JSON)
        prompt = f"""
        Extract a short task title (max 3 words).

        Input: "{user_input}"

        Output ONLY JSON:
        {{
            "title": "..."
        }}
        """

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
                ],
                "temperature": 0  # 🔥 reduce randomness
            }
        )

        result = response.json()
        print("DEBUG RESPONSE:", result)

        # 🔥 HANDLE API ERROR
        if "error" in result:
            raise ValueError(result["error"]["message"])

        content = result["choices"][0]["message"]["content"]

        print("RAW OUTPUT:", content)

        # 🔥 CLEAN RESPONSE
        content = content.replace("```json", "").replace("```", "").strip()

        # 🔥 EXTRACT JSON ONLY
        match = re.search(r"\{.*\}", content, re.DOTALL)

        if match:
            data = json.loads(match.group())
            title = data.get("title", "Task")
        else:
            raise ValueError("No JSON found")

    except Exception as e:
        print("ERROR:", str(e))

        # 🔥 FALLBACK TITLE FROM INPUT
        words = user_input.lower().split()
        title = " ".join(words[:2]).title()

    # 🔥 ALWAYS HANDLE TIME IN PYTHON
    now = datetime.now()

    if "minute" in user_input:
        minutes = int(re.search(r"\d+", user_input).group())
        scheduled_time = now + timedelta(minutes=minutes)

    elif "hour" in user_input:
        hours = int(re.search(r"\d+", user_input).group())
        scheduled_time = now + timedelta(hours=hours)

    else:
        scheduled_time = now + timedelta(minutes=1)

    return {
        "title": title,
        "time": scheduled_time.isoformat()
    }