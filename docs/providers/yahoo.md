# Yahoo Mail (IMAP)

- Server IMAP: `imap.mail.yahoo.com`
- Porta: `993` (SSL)
- Utente: il tuo indirizzo Yahoo (es. `nome@yahoo.it`)
- Password: **App Password** (richiede 2FA)

**Passi**:
1. Attiva **verifica in due passaggi** su Yahoo.
2. Genera una **App Password** per IMAP.
3. Configura `.env`:
   ```ini
   IMAP_HOST=imap.mail.yahoo.com
   IMAP_USER=tuoaccount@yahoo.it
   IMAP_PASS=<app-password>
   IMAP_MAILBOX=INBOX
   ```
