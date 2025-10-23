import time, json, os
from sqlalchemy import text
from db import engine
from ai import classify_email

MAX_ATTEMPTS = 3

def fetch_job(cx):
    row = cx.execute(text("""
        SELECT id, email_id FROM email_queue
        WHERE status='pending'
        ORDER BY id ASC
        LIMIT 1
        FOR UPDATE
    """)).fetchone()
    return row

def process_one():
    with engine.begin() as cx:
        job = fetch_job(cx)
        if not job:
            return False
        jid, email_id = job
        cx.execute(text("UPDATE email_queue SET status='processing' WHERE id=:id"), {"id": jid})
        email_row = cx.execute(text("""
            SELECT subject, from_address, body_text FROM emails_raw WHERE id=:id
        """), {"id": email_id}).fetchone()
    if not email_row:
        with engine.begin() as cx:
            cx.execute(text("UPDATE email_queue SET status='error', error_msg='email not found' WHERE id=:id"), {"id": jid})
        return True

    subject = email_row[0] or ""
    from_addr = email_row[1] or ""
    body = email_row[2] or ""

    try:
        data, model = classify_email(subject, from_addr, body)
        with engine.begin() as cx:
            cx.execute(text("""
                INSERT INTO email_ai (email_id,intent,confidence,priority,entities,model)
                VALUES (:id,:intent,:conf,:prio,:entities,:model)
                ON DUPLICATE KEY UPDATE intent=:intent,confidence=:conf,priority=:prio,entities=:entities,model=:model
            """), {
                "id": email_id,
                "intent": data.get("intent","other"),
                "conf": float(data.get("confidence",0.0) or 0.0),
                "prio": data.get("priority","normal"),
                "entities": json.dumps(data.get("entities",{})),
                "model": model
            })
            cx.execute(text("UPDATE email_queue SET status='done', error_msg=NULL WHERE id=:id"), {"id": jid})
    except Exception as e:
        with engine.begin() as cx:
            cx.execute(text("""
                UPDATE email_queue
                SET status = CASE WHEN attempts+1>=:max THEN 'error' ELSE 'pending' END,
                    attempts = attempts + 1,
                    error_msg = :msg
                WHERE id=:id
            """), {"id": jid, "msg": str(e), "max": MAX_ATTEMPTS})
    return True

def main():
    processed = 0
    while processed < 50:
        ok = process_one()
        if not ok:
            break
        processed += 1

if __name__ == "__main__":
    main()
