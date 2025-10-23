import os, email
from datetime import datetime, timezone
from dotenv import load_dotenv
from imapclient import IMAPClient
from email.header import decode_header, make_header
from bs4 import BeautifulSoup
from db import insert_email, upsert_run, get_run

load_dotenv()
HOST = os.getenv("IMAP_HOST")
USER = os.getenv("IMAP_USER")
PASS = os.getenv("IMAP_PASS")
MAILBOX = os.getenv("IMAP_MAILBOX","INBOX")
PROVIDER = os.getenv("PROVIDER_LABEL","imap")
MAILBOX_LABEL = os.getenv("MAILBOX_LABEL", USER)

def as_text(msg):
    body_txt, body_html, has_attach = "", "", False
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if ctype == "text/plain" and "attachment" not in disp:
                body_txt += (part.get_payload(decode=True) or b"").decode(part.get_content_charset() or "utf-8", "ignore")
            elif ctype == "text/html" and "attachment" not in disp:
                body_html += (part.get_payload(decode=True) or b"").decode(part.get_content_charset() or "utf-8", "ignore")
            elif part.get_filename():
                has_attach = True
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body_txt = payload.decode(msg.get_content_charset() or "utf-8", "ignore")
    snippet_src = body_txt or (BeautifulSoup(body_html, "html.parser").get_text("\n") if body_html else "")
    return body_txt, body_html, has_attach, (snippet_src[:500] if snippet_src else None)

def decode_subj(s):
    try:
        return str(make_header(decode_header(s or "")))[:500]
    except Exception:
        return (s or "")[:500]

def main():
    last_uid_str = get_run(PROVIDER, MAILBOX_LABEL, "imap_uid")
    last_uid = int(last_uid_str) if last_uid_str else None

    with IMAPClient(HOST, use_uid=True, ssl=True) as server:
        server.login(USER, PASS)
        server.select_folder(MAILBOX)
        if last_uid:
            uids = server.search([u'UID', f'{last_uid+1}:*'])
        else:
            all_uids = server.search(['ALL'])
            uids = sorted(all_uids)[-200:]

        for uid in uids:
            raw = server.fetch([uid], ['RFC822'])[uid][b'RFC822']
            msg = email.message_from_bytes(raw)
            message_id = msg.get("Message-ID")
            subject = decode_subj(msg.get("Subject"))
            from_addr = email.utils.parseaddr(msg.get("From"))[1]
            from_name = email.utils.parseaddr(msg.get("From"))[0] or None
            to_addrs = [email.utils.parseaddr(x)[1] for x in msg.get_all("To", [])] if msg.get_all("To") else []
            cc_addrs = [email.utils.parseaddr(x)[1] for x in msg.get_all("Cc", [])] if msg.get_all("Cc") else []
            date_val = msg.get("Date")
            try:
                dt = email.utils.parsedate_to_datetime(date_val) if date_val else datetime.now(timezone.utc)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            except Exception:
                dt = datetime.now(timezone.utc)

            body_txt, body_html, has_att, snippet = as_text(msg)

            insert_email(
                provider=PROVIDER, mailbox=MAILBOX_LABEL, message_id=message_id, uid=uid, external_id=None,
                from_addr=from_addr, from_name=from_name, to_list=to_addrs, cc_list=cc_addrs, subject=subject,
                snippet=snippet, body_text=body_txt, body_html=body_html, received_at=dt, has_attachments=has_att
            )
            upsert_run(PROVIDER, MAILBOX_LABEL, "imap_uid", str(uid))

        server.logout()

if __name__ == "__main__":
    main()
