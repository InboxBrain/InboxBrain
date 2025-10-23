import os, subprocess, threading
from typing import Optional
from fastapi import FastAPI, Depends, Body, HTTPException, Request
from sqlalchemy import text
from db import engine

app = FastAPI()

def auth(req: Request):
    token = req.headers.get("x-api-token")
    expected = os.getenv("API_TOKEN", "changeme")
    if not token or token != expected:
        raise HTTPException(status_code=401, detail="unauthorized")
    return True

@app.get("/health")
def health():
    with engine.connect() as cx:
        cx.execute(text("SELECT 1"))
    return {"ok": True}

@app.get("/emails")
def list_emails(limit: int = 50, intent: Optional[str] = None):
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
    return {"items": [dict(r) for r in rows]}

@app.get("/emails/{email_id}", dependencies=[Depends(auth)])
def get_email(email_id: int):
    q = '''
    SELECT e.*, a.intent, a.confidence, a.model
    FROM emails_raw e
    LEFT JOIN email_ai a ON a.email_id = e.id
    WHERE e.id = :id
    LIMIT 1;
    '''
    with engine.connect() as cx:
        row = cx.execute(text(q), {"id": email_id}).mappings().fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="email not found")
        return dict(row)

@app.get("/queue", dependencies=[Depends(auth)])
def list_queue(limit: int = 200, status: Optional[str] = None):
    q = "SELECT id, email_id, status, attempts, error_msg, created_at, updated_at FROM email_queue"
    params = {"limit": limit}
    if status:
        q += " WHERE status=:status"
        params["status"] = status
    q += " ORDER BY updated_at DESC LIMIT :limit"
    with engine.connect() as cx:
        rows = cx.execute(text(q), params).mappings().all()
        return {"items": [dict(r) for r in rows]}

@app.post("/requeue/{queue_id}", dependencies=[Depends(auth)])
def requeue(queue_id: int):
    with engine.begin() as cx:
        row = cx.execute(text("SELECT status FROM email_queue WHERE id=:id FOR UPDATE"), {"id": queue_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="queue item not found")
        cx.execute(text("UPDATE email_queue SET status='pending', attempts=0 WHERE id=:id"), {"id": queue_id})
    return {"ok": True, "id": queue_id}

@app.get("/admin/settings", dependencies=[Depends(auth)])
def get_settings():
    with engine.connect() as cx:
        rows = cx.execute(text("SELECT `key`,`value` FROM settings ORDER BY `key`")).mappings().all()
        return {r["key"]: r["value"] for r in rows}

@app.put("/admin/settings", dependencies=[Depends(auth)])
def put_settings(payload: dict = Body(...)):
    with engine.begin() as cx:
        for k, v in (payload or {}).items():
            cx.execute(text("INSERT INTO settings(`key`,`value`) VALUES(:k,:v) ON DUPLICATE KEY UPDATE `value`=:v"),
                       {"k": k, "v": str(v)})
    return {"ok": True, "updated": list(payload.keys())}

def _run_bg(script: str):
    def _t():
        subprocess.call(["python", script])
    threading.Thread(target=_t, daemon=True).start()

@app.post("/admin/run/ingest", dependencies=[Depends(auth)])
def run_ingest_now():
    _run_bg("run_ingestor_imap.py")
    return {"ok": True}

@app.post("/admin/run/worker", dependencies=[Depends(auth)])
def run_worker_now():
    _run_bg("run_worker_ai.py")
    return {"ok": True}

# Webhooks (simplified)
@app.post("/webhooks/sendgrid", dependencies=[Depends(auth)])
async def webhook_sendgrid(payload: dict):
    from sqlalchemy import text as sqltext
    from datetime import datetime
    provider = "sendgrid"
    mailbox = payload.get("to") or "inbound"
    from_addr = payload.get("from") or ""
    subject = payload.get("subject") or ""
    body_text = payload.get("text") or ""
    body_html = payload.get("html") or ""
    message_id = payload.get("Message-ID") or payload.get("message_id") or ""
    received_at = datetime.utcnow()
    with engine.begin() as cx:
        cx.execute(sqltext("""
            INSERT INTO emails_raw (provider, mailbox, message_id, uid, from_address, subject, body_text, body_html, received_at, hash_dedupe)
            VALUES (:provider, :mailbox, :message_id, 0, :from_address, :subject, :body_text, :body_html, :received_at,
                    SHA2(CONCAT(:from_address,'|',:subject,'|',LEFT(:body_text,1024)), 256))
            ON DUPLICATE KEY UPDATE updated_at=NOW()
        """), {
            "provider": provider, "mailbox": mailbox, "message_id": message_id,
            "from_address": from_addr, "subject": subject, "body_text": body_text,
            "body_html": body_html, "received_at": received_at
        })
        cx.execute(sqltext("""
            INSERT INTO email_queue (email_id, status, attempts)
            SELECT id, 'pending', 0 FROM emails_raw
            WHERE provider=:provider AND mailbox=:mailbox AND IFNULL(message_id,'')=:message_id
            ON DUPLICATE KEY UPDATE updated_at=NOW()
        """), {"provider": provider, "mailbox": mailbox, "message_id": message_id})
    return {"ok": True}

@app.post("/webhooks/mailgun", dependencies=[Depends(auth)])
async def webhook_mailgun(payload: dict):
    from sqlalchemy import text as sqltext
    from datetime import datetime
    provider = "mailgun"
    mailbox = payload.get("recipient") or "inbound"
    from_addr = payload.get("sender") or ""
    subject = payload.get("subject") or ""
    body_text = payload.get("body-plain") or ""
    body_html = payload.get("body-html") or ""
    message_id = payload.get("Message-Id") or payload.get("message-id") or ""
    received_at = datetime.utcnow()
    with engine.begin() as cx:
        cx.execute(sqltext("""
            INSERT INTO emails_raw (provider, mailbox, message_id, uid, from_address, subject, body_text, body_html, received_at, hash_dedupe)
            VALUES (:provider, :mailbox, :message_id, 0, :from_address, :subject, :body_text, :body_html, :received_at,
                    SHA2(CONCAT(:from_address,'|',:subject,'|',LEFT(:body_text,1024)), 256))
            ON DUPLICATE KEY UPDATE updated_at=NOW()
        """), {
            "provider": provider, "mailbox": mailbox, "message_id": message_id,
            "from_address": from_addr, "subject": subject, "body_text": body_text,
            "body_html": body_html, "received_at": received_at
        })
        cx.execute(sqltext("""
            INSERT INTO email_queue (email_id, status, attempts)
            SELECT id, 'pending', 0 FROM emails_raw
            WHERE provider=:provider AND mailbox=:mailbox AND IFNULL(message_id,'')=:message_id
            ON DUPLICATE KEY UPDATE updated_at=NOW()
        """), {"provider": provider, "mailbox": mailbox, "message_id": message_id})
    return {"ok": True}
