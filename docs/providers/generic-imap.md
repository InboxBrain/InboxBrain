# Provider generico IMAP

- Server IMAP: contatta il provider (quasi sempre SSL/993)
- Porta: 993 (SSL)
- Autenticazione: App Password/Token quando disponibile
- Posta: `INBOX`

**Note**:
- Evita polling eccessivo: >=60–120s.
- Se disponibile, abilita IMAP IDLE nel client per near-realtime.
