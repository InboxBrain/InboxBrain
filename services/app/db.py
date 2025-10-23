import hashlib, json, os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DB_DSN"), pool_pre_ping=True)

def sha256(s: str) -> str:
    import hashlib as _h
    return _h.sha256(s.encode("utf-8", "ignore")).hexdigest()

def upsert_run(provider: str, mailbox: str, ctype: str, value: str):
    with engine.begin() as cx:
        cx.execute(text("""
            INSERT INTO runs(provider, mailbox, checkpoint_type, checkpoint_value)
            VALUES (:p,:m,:t,:v)
            ON DUPLICATE KEY UPDATE checkpoint_value=:v
        """), {"p":provider, "m":mailbox, "t":ctype, "v":value})

def get_run(provider: str, mailbox: str, ctype: str):
    with engine.connect() as cx:
        row = cx.execute(text("""
            SELECT checkpoint_value FROM runs
            WHERE provider=:p AND mailbox=:m AND checkpoint_type=:t
        """), {"p":provider, "m":mailbox, "t":ctype}).first()
        return row[0] if row else None

def insert_email(provider, mailbox, message_id, uid, external_id,
                 from_addr, from_name, to_list, cc_list, subject,
                 snippet, body_text, body_html, received_at, has_attachments):
    dedupe_base = f"{from_addr}|{subject or ''}|{(body_text or body_html or '')[:1000]}"
    h = sha256(dedupe_base)
    with engine.begin() as cx:
        cx.execute(text("""
            INSERT IGNORE INTO emails_raw
            (provider, mailbox, message_id, uid, external_id, from_address, from_name,
             to_addresses, cc_addresses, subject, snippet, body_text, body_html,
             has_attachments, received_at, hash_dedupe)
            VALUES
            (:provider,:mailbox,:message_id,:uid,:external_id,:from_address,:from_name,
             :to_addresses,:cc_addresses,:subject,:snippet,:body_text,:body_html,
             :has_attachments,:received_at,:hash_dedupe)
        """), {
            "provider": provider, "mailbox": mailbox, "message_id": message_id, "uid": uid,
            "external_id": external_id, "from_address": from_addr, "from_name": from_name,
            "to_addresses": json.dumps(to_list or []), "cc_addresses": json.dumps(cc_list or []),
            "subject": subject, "snippet": snippet, "body_text": body_text, "body_html": body_html,
            "has_attachments": 1 if has_attachments else 0,
            "received_at": received_at, "hash_dedupe": h
        })
        row = cx.execute(text("""
            SELECT id FROM emails_raw
            WHERE provider=:provider AND mailbox=:mailbox
              AND COALESCE(message_id,'') = COALESCE(:message_id,'')
              AND COALESCE(external_id,'') = COALESCE(:external_id,'')
              AND COALESCE(uid,0) = COALESCE(:uid,0)
            ORDER BY id DESC LIMIT 1
        """), {
            "provider": provider, "mailbox": mailbox,
            "message_id": message_id, "external_id": external_id, "uid": uid
        }).first()
        email_id = row[0]
        cx.execute(text("""
            INSERT IGNORE INTO email_queue(email_id, status) VALUES (:eid, 'pending')
        """), {"eid": email_id})
        return email_id
