# Configurazione (.env)

Variabili principali:
- `DB_DSN` — DSN SQLAlchemy per MySQL nel compose: `mysql+mysqldb://app:app@mysql:3306/inboxbrain`
- `IMAP_HOST` — server IMAP (SSL, porta 993 di default)
- `IMAP_USER` — indirizzo email
- `IMAP_PASS` — **App Password** o token
- `IMAP_MAILBOX` — tipicamente `INBOX`
- `PROVIDER_LABEL` — etichetta provider (es. `imap`, `gmail`)
- `MAILBOX_LABEL` — etichetta casella (di solito l'email)
- `OPENAI_API_KEY` — chiave OpenAI
- `OPENAI_MODEL` — modello (default: `gpt-4o-mini`)
- `APP_ROLE` — `ingestor` | `worker` | `api` | `combo`
- `API_TOKEN` — token HTTP header `x-api-token` per le API

## Parametri consigliati (estendibili)
- `INGEST_SLEEP` — pausa tra run dell’ingestor (sec), es. `120`
- `WORKER_SLEEP` — pausa tra run del worker (sec), es. `30`
- `FIRST_RUN_BATCH` — quanti UID importare la primissima volta (default 200)
> Nota: per usare `INGEST_SLEEP`/`WORKER_SLEEP` serve la versione “parametrica” dell'`entrypoint.sh`.
