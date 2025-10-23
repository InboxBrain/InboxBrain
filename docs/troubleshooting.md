# Troubleshooting

## Porta 8000 occupata
Modifica `ports` in `docker-compose.yml`: `8080:8000` e riavvia.

## MySQL init error (schema)
Se vedi errori di sintassi sugli indici, assicurati di usare lo schema con **colonne generate** (`*_norm`).
Se serve rieseguire init, fai `docker compose down -v` per ricreare il volume.

## OpenAI error: 'responses' non esiste
Aggiorna `ai.py` a versione `chat.completions` (già presente) e pinna `httpx==0.27.2`.

## Coda in errore
Requeue:
```bash
UPDATE email_queue SET status='pending', attempts=0 WHERE status='error';
```
Poi rilancia il worker.

## Nessuna email importata
- Verifica `IMAP_HOST/USER/PASS` (App Password/Token).
- Controlla `IMAP_MAILBOX` (es. INBOX).
- Guarda i log dell’app.
