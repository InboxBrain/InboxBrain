import os, time, email, hashlib
from datetime import datetime
from email.header import decode_header, make_header
from imapclient import IMAPClient
from sqlalchemy import text
from db import engine

IMAP_HOST = os.getenv("IMAP_HOST")
IMAP_USER = os.getenv("IMAP_USER")
IMAP_PASS = os.getenv("IMAP_PASS")
IMAP_MAILBOX = os.getenv("IMAP_MAILBOX", "INBOX")
PROVIDER_LABEL = os.getenv("PROVIDER_LABEL", "imap")
MAILBOX_LABEL = os.getenv("MAILBOX_LABEL", IMAP_USER or "inbox")
IDLE_TIMEOUT = int(os.getenv("IMAP_IDLE_TIMEOUT","600"))

def norm(s):
    if not s: return ""
    try: return str(make_header(decode_header(s)))
    except Exception: return s

def extract_text(msg):
    body_text, body_html = None, None
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cd = str(part.get('Content-Disposition') or '').lower()
            if ctype == "text/plain" and "attachment" not in cd:
                try:
                    body_text = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="ignore")
                except Exception: pass
            elif ctype == "text/html" and "attachment" not in cd:
                try:
                    body_html = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="ignore")
                except Exception: pass
    else:
        ctype = msg.get_content_type()
        try:
            payload = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="ignore")
        except Exception:
            payload = ""
        if ctype == "text/plain": body_text = payload
        elif ctype == "text/html": body_html = payload
    return body_text, body_html

def main():
    with IMAPClient(IMAP_HOST, ssl=True) as server:
        server.login(IMAP_USER, IMAP_PASS)
        server.select_folder(IMAP_MAILBOX)
        print("IMAP IDLE attivo su", IMAP_MAILBOX)
        while True:
            try:
                server.idle()
                server.idle_check(timeout=IDLE_TIMEOUT)
                server.idle_done()
                uids = server.search(["UNSEEN"])
                if not uids:
                    continue
                msg_data = server.fetch(uids, ["RFC822"])
                for uid, data in msg_data.items():
                    raw = data[b"RFC822"]
                    msg = email.message_from_bytes(raw)
                    msgid = msg.get("Message-ID") or ""
                    from_addr = str(make_header(decode_header(msg.get('From') or '')))
                    subject = norm(msg.get("Subject"))
                    date_hdr = msg.get("Date")
                    try:
                        received_at = datetime.strptime(date_hdr[:31], "%a, %d %b %Y %H:%M:%S %z").astimezone().replace(tzinfo=None)
                    except Exception:
                        received_at = datetime.utcnow()
                    body_text, body_html = extract_text(msg)
                    hash_src = f"{from_addr}|{subject}|{(body_text or '')[:1024]}".encode("utf-8","ignore")
                    hash_dedupe = hashlib.sha256(hash_src).hexdigest()
                    with engine.begin() as cx:
                        cx.execute(text("""
                            INSERT INTO emails_raw
                              (provider, mailbox, message_id, uid, from_address, subject, body_text, body_html, received_at, hash_dedupe)
                            VALUES
                              (:provider, :mailbox, :message_id, :uid, :from_address, :subject, :body_text, :body_html, :received_at, :hash_dedupe)
                            ON DUPLICATE KEY UPDATE updated_at=NOW()
                        """), {
                            "provider": PROVIDER_LABEL, "mailbox": MAILBOX_LABEL, "message_id": msgid or "", "uid": int(uid),
                            "from_address": from_addr or "", "subject": subject or "", "body_text": body_text or "",
                            "body_html": body_html or "", "received_at": received_at, "hash_dedupe": hash_dedupe
                        })
                        cx.execute(text("""
                            INSERT INTO email_queue (email_id, status, attempts)
                            SELECT id, 'pending', 0 FROM emails_raw
                            WHERE provider=:provider AND mailbox=:mailbox AND IFNULL(message_id,'')=:message_id AND IFNULL(uid,0)=:uid
                            ON DUPLICATE KEY UPDATE updated_at=NOW()
                        """), {"provider": PROVIDER_LABEL, "mailbox": MAILBOX_LABEL, "message_id": msgid or "", "uid": int(uid)})
            except Exception as e:
                print("IMAP IDLE errore:", e)
                time.sleep(5)

if __name__ == "__main__":
    main()
