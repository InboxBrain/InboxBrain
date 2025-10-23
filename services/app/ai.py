import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Puoi cambiare modello da .env con OPENAI_MODEL=gpt-4o-mini (default sotto)
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM = """Sei un assistente che classifica email e restituisce SOLO JSON valido.
Classi ammesse:
- quotation
- support_request
- invoice
- job_application
- spam
- other

Schema atteso:
{
  "intent": "quotation|support_request|invoice|job_application|spam|other",
  "confidence": 0.0-1.0,
  "priority": "low|normal|high|urgent",
  "entities": {
    "full_name": "...",
    "company": "...",
    "email": "...",
    "phone": "...",
    "order_id": "...",
    "amount": {"value": 123.45, "currency": "EUR"},
    "due_date": "YYYY-MM-DD"
  }
}
Rispondi esclusivamente con un JSON.
"""

def classify_email(subject: str, from_addr: str, body: str):
    """
    Ritorna (dict_json, model_name)
    """
    content = f"From: {from_addr}\nSubject: {subject or ''}\n\n{body or ''}"

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": content},
        ],
        # Chiediamo un JSON ben formato
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    text = resp.choices[0].message.content or "{}"

    # Parsing robusto con fallback sicuro
    try:
        data = json.loads(text)
    except Exception:
        data = {"intent": "other", "confidence": 0.0, "priority": "normal", "entities": {}}

    # Normalizzazioni leggere per evitare KeyError a valle
    if "intent" not in data or not isinstance(data["intent"], str):
        data["intent"] = "other"
    data.setdefault("confidence", 0.0)
    data.setdefault("priority", "normal")
    data.setdefault("entities", {})

    return data, MODEL
