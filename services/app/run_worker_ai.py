import json
from sqlalchemy import text
from db import engine
from ai import classify_email

def fetch_job(conn):
    row = conn.execute(text('''
      SELECT q.id, e.id AS email_id, e.subject, e.from_address, COALESCE(e.body_text, e.body_html) AS body
      FROM email_queue q
      JOIN emails_raw e ON e.id = q.email_id
      WHERE q.status='pending'
      ORDER BY q.id
      LIMIT 1
      FOR UPDATE
    ''')).mappings().first()
    if not row:
        return None
    conn.execute(text("UPDATE email_queue SET status='processing', locked_at=NOW() WHERE id=:id"), {"id": row["id"]})
    return row

def mark_done(conn, qid):
    conn.execute(text("UPDATE email_queue SET status='done' WHERE id=:id"), {"id": qid})

def mark_error(conn, qid, msg):
    conn.execute(text("UPDATE email_queue SET status='error', attempts=attempts+1, error_msg=:m WHERE id=:id"),
                 {"id": qid, "m": msg[:1000]})

def upsert_category(conn, name: str):
    if not name: return None
    conn.execute(text("INSERT IGNORE INTO email_categories(name) VALUES (:n)"), {"n": name})
    row = conn.execute(text("SELECT id FROM email_categories WHERE name=:n"), {"n": name}).first()
    return row[0] if row else None

def save_ai(conn, email_id, model, result):
    cat_id = upsert_category(conn, result.get("intent"))
    conn.execute(text('''
      INSERT INTO email_ai(email_id, model_name, intent, confidence, category_id, extracted_json)
      VALUES (:eid,:model,:intent,:conf,:cat,:json)
      ON DUPLICATE KEY UPDATE
        model_name=VALUES(model_name),
        intent=VALUES(intent),
        confidence=VALUES(confidence),
        category_id=VALUES(category_id),
        extracted_json=VALUES(extracted_json)
    '''), {
      "eid": email_id,
      "model": model,
      "intent": result.get("intent"),
      "conf": result.get("confidence"),
      "cat": cat_id,
      "json": json.dumps(result, ensure_ascii=False)
    })

def main():
    with engine.begin() as cx:
        job = fetch_job(cx)
        if not job:
            print("Queue empty.")
            return
        qid = job["id"]
        try:
            result, model = classify_email(job["subject"], job["from_address"], job["body"])
            save_ai(cx, job["email_id"], model, result)
            mark_done(cx, qid)
            print(f"Processed email_id={job['email_id']} intent={result.get('intent')}")
        except Exception as e:
            mark_error(cx, qid, str(e))
            print("Error:", e)

if __name__ == "__main__":
    main()
