import requests
import os
import json
import re
from datetime import datetime, timedelta

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"


def _extract_number(text: str) -> int | None:
    """Safely extract the first integer from a string."""
    match = re.search(r"\d+", text)
    return int(match.group()) if match else None


def _parse_time(user_input: str) -> datetime:
    """
    Parse time expressions from natural language.
    Handles: seconds, minutes, hours, days.
    Falls back to 5 minutes if nothing recognized.
    """
    text = user_input.lower()
    now = datetime.now()

    if "second" in text:
        n = _extract_number(text) or 30
        return now + timedelta(seconds=n)

    if "minute" in text or "min" in text:
        n = _extract_number(text) or 5
        return now + timedelta(minutes=n)

    if "hour" in text:
        n = _extract_number(text) or 1
        return now + timedelta(hours=n)

    if "day" in text:
        n = _extract_number(text) or 1
        return now + timedelta(days=n)

    if "tomorrow" in text:
        return now + timedelta(days=1)

    if "tonight" in text or "night" in text:
        tonight = now.replace(hour=21, minute=0, second=0, microsecond=0)
        return tonight if tonight > now else now + timedelta(hours=1)

    # Default: 5 minutes
    return now + timedelta(minutes=5)


def _call_groq(user_input: str) -> str:
    """Call Groq API to extract a task title. Returns extracted title or raises."""
    prompt = f"""Extract a concise task title (2-4 words) from this input.

Input: "{user_input}"

Rules:
- Use action words (e.g., "Drink Water", "Call Mom", "Submit Report")
- Max 4 words
- No punctuation

Output ONLY valid JSON, nothing else:
{{"title": "..."}}"""

    response = requests.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 50,
        },
        timeout=10,
    )

    response.raise_for_status()
    result = response.json()

    if "error" in result:
        raise ValueError(f"Groq API error: {result['error']['message']}")

    return result["choices"][0]["message"]["content"]


def _extract_title_from_groq(user_input: str) -> str:
    """Call Groq and safely parse the title from JSON response."""
    try:
        raw = _call_groq(user_input)
        raw = raw.replace("```json", "").replace("```", "").strip()

        match = re.search(r"\{.*?\}", raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            title = data.get("title", "").strip()
            if title:
                return title

        raise ValueError("Could not parse title from Groq response")

    except Exception as e:
        print(f"[AI Parser] Groq failed: {e} — using fallback title")
        # Fallback: take first 3 meaningful words, skip filler
        stop_words = {"remind", "me", "to", "please", "in", "at", "after", "a", "an", "the"}
        words = [w for w in user_input.lower().split() if w not in stop_words]
        return " ".join(words[:3]).title() or "New Task"


def parse_command(user_input: str) -> dict:
    """
    Parse a natural language command into a task dict.

    Returns:
        {"title": str, "time": ISO 8601 string}
    """
    title = _extract_title_from_groq(user_input)
    scheduled_time = _parse_time(user_input)

    print(f"[AI Parser] '{user_input}' → title='{title}', time={scheduled_time.isoformat()}")

    return {
        "title": title,
        "time": scheduled_time.isoformat(),
    }
