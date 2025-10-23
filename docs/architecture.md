# Architettura

**Componenti**:
- **MySQL**: persistenza (`emails_raw`, `email_queue`, `email_ai`, `runs`, `email_attachments`, `email_categories`).
- **App** (container unico) con tre ruoli:
  - **API** (FastAPI) — endpoint `/health`, `/emails`.
  - **Ingestor (IMAP)** — legge la casella, normalizza, salva, aggiorna `runs`.
  - **Worker AI** — classifica dalla coda e salva in `email_ai`.
- **EntryPoint**: esecuzione in loop (combo) oppure servizi separati.

**Flusso**:
1. Ingestor connette IMAP (SSL/993), legge nuovi UID rispetto a `runs(imap_uid)`, inserisce in `emails_raw` e crea item in `email_queue`.
2. Worker AI preleva `pending`, chiama OpenAI, salva `intent/confidence/extracted_json` in `email_ai`, marca `done`.
3. API espone consultazione email + risultati AI.

**Idempotenza**:
- `emails_raw` ha `UNIQUE KEY` su `(provider, mailbox, message_id_norm, external_id_norm, uid_norm)`.
- `hash_dedupe` come rete di sicurezza.
