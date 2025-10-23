# InboxBrain

InboxBrain legge email da qualsiasi provider IMAP, le classifica con AI e popola MySQL con:
- `emails_raw` (ingest normalizzato)
- `email_queue` (coda su DB)
- `email_ai` (risultato AI)
- `runs` (checkpoint per dedup/continuità)

## Avvio rapido

1. Copia `.env.example` in `.env` e compila le variabili (IMAP + OPENAI).
2. Avvia:
   ```bash
   docker compose up -d --build
   ```
3. Verifica MySQL e API:
   - Health: `curl http://localhost:8000/health`
   - Elenco email (richiede header): `curl -H "x-api-token: changeme" "http://localhost:8000/emails?limit=20"`

> Per la prima run l'ingestor prende **gli ultimi 200 UID**; poi prosegue incrementale con `runs(checkpoint_type='imap_uid')`.

## Config

- `APP_ROLE` nel `.env` può essere:
  - `ingestor` → solo ingest IMAP
  - `worker` → solo classificazione AI
  - `api` → solo API
  - `combo` (default) → tutto insieme (dev mode)

## Note

- Dedup: chiave unica su `(provider, mailbox, message_id, external_id, uid)` + `hash_dedupe` fallback.
- Allegati: tabella `email_attachments` predisposta (salvataggio file non incluso di default).
- Sicurezza API: semplice token `x-api-token` (base per demo).

## Estensioni suggerite

- Ingest Gmail via API Watch/Pub/Sub con `runs(checkpoint_type='gmail_history_id')`.
- Regole di routing (auto-reply, assegnazioni).
- OCR/estrazione PDF per allegati.
- Dashboard (Metabase/Superset) collegata a MySQL.




## Esempio utilizzo

Perfetto! Ecco i passaggi “click-by-click” per avviare **InboxBrain** usando **Yahoo** come casella IMAP di test.

---

# 1) Prerequisiti rapidi

* **Docker** e **Docker Compose** installati.
* Su **Yahoo**: attiva l’Autenticazione a due fattori e crea una **App Password** (non usare la password normale).
  IMAP Yahoo: `imap.mail.yahoo.com` porta `993` (SSL).

---

# 2) Scarica e prepara il progetto

1. Scarica lo zip (quello con il `.gitignore` già incluso):

   * [InboxBrain_with_gitignore.zip](sandbox:/mnt/data/InboxBrain_with_gitignore.zip)

2. Estrailo, entra nella cartella `InboxBrain/`.

3. Crea il file `.env` partendo dall’esempio:

```bash
cp .env.example .env
```

4. Modifica **.env** con i tuoi dati Yahoo e la chiave OpenAI:

```ini
# Connessione DB (già ok col compose)
DB_DSN=mysql+mysqldb://app:app@mysql:3306/inboxbrain

# Yahoo IMAP
IMAP_HOST=imap.mail.yahoo.com
IMAP_USER=la-tua-mail@yahoo.it          # <-- la tua email Yahoo
IMAP_PASS=la-tua-app-password           # <-- la App Password Yahoo
IMAP_MAILBOX=INBOX

# Etichette utili per checkpoint
PROVIDER_LABEL=imap
MAILBOX_LABEL=la-tua-mail@yahoo.it

# OpenAI (per la classificazione AI)
OPENAI_API_KEY=sk-...                   # <-- la tua chiave

# Esegui tutto in un container (API + ingestor + worker)
APP_ROLE=combo

# Token API (per chiamare gli endpoint)
API_TOKEN=changeme
```

> Nota: la **prima run** importa **gli ultimi 200** messaggi della mailbox e poi prosegue in modo incrementale usando il checkpoint `runs(imap_uid)`.

---

# 3) Avvio con Docker

Dalla root del progetto:

```bash
docker compose up -d --build
```

Questo avvia:

* **mysql:8** (crea auto le tabelle tramite `db/schema.sql`)
* **app** (FastAPI + ingestor IMAP + worker AI, perché `APP_ROLE=combo`)

Controlla i log:

```bash
docker compose logs -f app
```

Vedrai messaggi tipo:

* “MySQL is ready.”
* Loop `run_ingestor_imap.py` (importa email)
* Loop `run_worker_ai.py` (classifica e scrive in `email_ai`)

---

# 4) Verifica che tutto giri

### API health

```bash
curl http://localhost:8000/health
# atteso: {"ok": true}
```

### Vedi le email normalizzate (con token)

```bash
curl -H "x-api-token: changeme" "http://localhost:8000/emails?limit=20"
```

Se la classificazione è già partita, vedrai anche `intent` e `confidence` uniti ai record.

---

# 5) Capire il flusso (in parole semplici)

* **Ingestor IMAP**: legge la INBOX Yahoo, salva in `emails_raw`, mette in coda `email_queue`, aggiorna `runs(imap_uid)`.
* **Worker AI**: prende dalla coda, chiama l’AI e scrive il risultato in `email_ai` (include `intent`, `confidence`, `extracted_json`), poi marca la coda come `done`.
* **API**: espone `/emails` per consultare i risultati.

---

# 6) Comandi utili (debug / ispezione)

### Log in tempo reale

```bash
docker compose logs -f app
```

### Entrare nella MySQL del container

```bash
docker exec -it inboxbrain-mysql mysql -uapp -papp inboxbrain
```

Esempi query:

```sql
SELECT COUNT(*) FROM emails_raw;
SELECT id, intent, confidence FROM email_ai ORDER BY id DESC LIMIT 10;
SELECT * FROM runs;
```

### Riavvio “pulito”

```bash
docker compose down
docker compose up -d
```

---

# 7) Problemi comuni (e soluzioni)

* **AUTH fallita su Yahoo**: quasi sempre è perché stai usando la password normale. Serve la **App Password** (con 2FA attivo).
* **Nessuna email importata**: controlla `IMAP_MAILBOX=INBOX`, e nei log di `app` che si connetta davvero.
* **AI non classifica**: verifica che `OPENAI_API_KEY` sia impostata; il worker gira ogni ~30s in modalità `combo`.
* **Porta 8000 occupata**: cambia il mapping in `docker-compose.yml` per l’app (es. `8080:8000`) e richiama gli endpoint su `http://localhost:8080`.

---

# 8) Varianti di esecuzione (facoltative)

* Solo **ingestor**:

  * `.env → APP_ROLE=ingestor`
  * `docker compose up -d --build`
* Solo **worker**:

  * `.env → APP_ROLE=worker`
* Solo **API**:

  * `.env → APP_ROLE=api`

In ambienti “prod” si tengono servizi separati (più pulito per scalare).

---

Se vuoi, posso:

* ridurre gli **“ultimi 200 UID”** (prima run) a un numero diverso (es. 50),
* aggiungere un **filtro per data** (es. importa solo ultimi X giorni),
* o includere un **endpoint webhook** (SendGrid/Mailgun) per testare anche senza IMAP.
