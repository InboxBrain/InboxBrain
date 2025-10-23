# Guida rapida (Docker)

1. **Clona/estrai** il progetto e crea `.env` partendo da `.env.example`.
2. **Imposta** variabili principali:
   ```ini
   DB_DSN=mysql+mysqldb://app:app@mysql:3306/inboxbrain
   IMAP_HOST=imap.mail.yahoo.com
   IMAP_USER=you@example.com
   IMAP_PASS=app-password   # App Password, non password normale
   IMAP_MAILBOX=INBOX
   OPENAI_API_KEY=sk-...
   APP_ROLE=combo
   API_TOKEN=changeme
   ```
3. **Avvia**:
   ```bash
   docker compose up -d --build
   ```
4. **Verifica**:
   ```bash
   curl http://localhost:8000/health
   curl -H "x-api-token: changeme" "http://localhost:8000/emails?limit=20"
   ```
5. **Run manuale** (facoltativo):
   ```bash
   docker exec -it inboxbrain-app bash -lc 'python run_ingestor_imap.py && python run_worker_ai.py'
   ```
