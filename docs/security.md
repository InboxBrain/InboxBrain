# Sicurezza

- **App Password/Token** per IMAP (non usare password normali). Abilita 2FA sul provider.
- **API Token** per endpoint interni (in produzione preferisci JWT/OPA e TLS).
- **PII**: se richiesto, cifra dati sensibili a livello applicativo o colonna.
- **Least privilege**: DB user dedicato (già configurato). Backup regolari.
- **Quote AI**: imposta limiti o rate per evitare costi imprevisti.
