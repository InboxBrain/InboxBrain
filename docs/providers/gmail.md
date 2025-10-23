# Gmail (IMAP)

- Server IMAP: `imap.gmail.com`
- Porta: `993` (SSL)
- Utente: indirizzo Gmail
- Password: **App Password** (richiede 2FA, account personale)

**Nota**: Google ha dismesso l'accesso "meno sicuro". Usa App Password. Per account Workspace con policy restrittive potresti dover abilitare IMAP dall'admin.

### Alternativa pro: Gmail API (Watch/Pub/Sub)
- Vantaggi: near-realtime, niente polling aggressivo.
- Meccanismo: `watch` → Pub/Sub → `history.list` → fetch nuovi messaggi.
- Checkpoint: `runs(checkpoint_type='gmail_history_id')`.

(Nel progetto attuale è incluso solo IMAP; l'ingestor API si può aggiungere come estensione.)
