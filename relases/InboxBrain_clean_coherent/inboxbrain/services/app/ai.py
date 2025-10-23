import os, json, time
from typing import Tuple
from sqlalchemy import text
from openai import OpenAI
from db import engine

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI()

_PROMPT_CACHE = {"value": None, "ts": 0.0}
_PROMPT_TTL = 60.0

DEFAULT_SYSTEM_PROMPT = (
    "Sei un assistente che classifica email e restituisce SOLO JSON valido. "
    "Classi ammesse: quotation, support_request, invoice, job_application, spam, other. "
    "Schema atteso: {\"intent\":\"...\", \"confidence\": 0-1, \"priority\": \"...\", \"entities\": {}}. "
    "Rispondi esclusivamente con un JSON."
)

def get_system_prompt() -> str:
    now = time.time()
    if _PROMPT_CACHE["value"] is not None and (now - _PROMPT_CACHE["ts"] < _PROMPT_TTL):
        return _PROMPT_CACHE["value"]
    prompt = None
    try:
        with engine.connect() as cx:
            row = cx.execute(text("SELECT `value` FROM settings WHERE `key`='AI_PROMPT' LIMIT 1;")).fetchone()
            if row and row[0]:
                prompt = row[0]
    except Exception:
        prompt = None
    if not prompt:
        prompt = DEFAULT_SYSTEM_PROMPT
    _PROMPT_CACHE["value"] = prompt
    _PROMPT_CACHE["ts"] = now
    return prompt

def classify_email(subject: str, from_addr: str, body: str) -> Tuple[dict, str]:
    system_prompt = get_system_prompt()
    content = f"From: {from_addr}\nSubject: {subject or ''}\n\n{body or ''}"
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role":"system","content": system_prompt},
                {"role":"user","content": content},
            ],
            response_format={"type":"json_object"},
            temperature=0.2,
        )
        text_out = resp.choices[0].message.content or "{}"
    except Exception:
        text_out = "{}"
    try:
        data = json.loads(text_out)
    except Exception:
        data = {"intent":"other","confidence":0.0,"priority":"normal","entities":{}}
    data.setdefault("intent","other")
    data.setdefault("confidence",0.0)
    data.setdefault("priority","normal")
    data.setdefault("entities",{})
    return data, MODEL
