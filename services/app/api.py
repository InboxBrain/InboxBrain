import os
from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy import text
from db import engine

API_TOKEN = os.getenv("API_TOKEN", "changeme")

app = FastAPI(title="InboxBrain API")

def auth(x_api_token: str = Header(None)):
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

@app.get("/health")
def health():
    with engine.connect() as cx:
        cx.execute(text("SELECT 1"))
    return {"ok": True}

@app.get("/emails")
def emails(limit: int = 50, intent: str | None = None, auth_ok: bool = Depends(auth)):
    q = '''
    SELECT e.id, e.from_address, e.subject, e.received_at, a.intent, a.confidence
    FROM emails_raw e
    LEFT JOIN email_ai a ON a.email_id = e.id
    '''
    params = {"limit": limit}
    if intent:
        q += " WHERE a.intent=:intent"
        params["intent"] = intent
    q += " ORDER BY e.received_at DESC LIMIT :limit"
    with engine.connect() as cx:
        rows = cx.execute(text(q), params).mappings().all()
    return {"items": list(rows)}
