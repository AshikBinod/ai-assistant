import requests
import os
import json
import re

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def parse_command(user_input):
    # 🔥 Stronger prompt for cleaner titles
    prompt = f"""
    You are an AI assistant that extracts tasks.

    RULES:
    - Extract ONLY the core action as title (1–2 words)
    - Remove phrases like "remind me", "check", "please"
    - Keep it clean and concise
    - Capitalize properly

    Examples:
    - "remind me to study at 10 pm" → "Study"
    - "check my workout in 30 minutes" → "Workout"
    - "finish RCC revision at 6 pm" → "RCC Revision"

    Input:
    "{user_input}"

    Return STRICT JSON only:
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

        # 🔥 Handle API errors
        if "error" in result:
            raise ValueError(result["error"]["message"])

        content = result["choices"][0]["message"]["content"]
        print("RAW OUTPUT:", content)

        # 🔥 Remove markdown artifacts
        content = content.replace("```json", "").replace("```", "").strip()

        # 🔥 Extract JSON block
        match = re.search(r"\{.*\}", content, re.DOTALL)

        if match:
            parsed = json.loads(match.group())

            # 🔥 Safety cleanup (extra protection)
            title = parsed.get("title", "Task").strip()
            time = parsed.get("time")

            # Basic cleanup of title
            title = title.replace("Remind me to", "").strip()

            return {
                "title": title,
                "time": time
            }

        else:
            raise ValueError("No JSON found")

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "title": "Fallback Task",
            "time": "2026-04-07T22:00:00"
        }