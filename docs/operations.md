# Operatività

## Modalità "combo"
Con `APP_ROLE=combo` l’entrypoint avvia API + loop:
- Ingestor ogni ~60s (configurabile)
- Worker ogni ~30s (configurabile)

## Modalità separate
Imposta `APP_ROLE` a `ingestor`, `worker` o `api` per container con ruolo singolo.

## Comandi utili
- **Log**: `docker compose logs -f app`
- **Stato DB**:
  ```bash
  docker exec -it inboxbrain-mysql mysql -uapp -papp inboxbrain -e "SHOW TABLES;"
  docker exec -it inboxbrain-mysql mysql -uapp -papp inboxbrain -e "SELECT status, COUNT(*) FROM email_queue GROUP BY status;"
  ```
- **Forza una run**:
  ```bash
  docker exec -it inboxbrain-app bash -lc 'python run_ingestor_imap.py && python run_worker_ai.py'
  ```
- **Requeue errori**:
  ```bash
  docker exec -it inboxbrain-mysql mysql -uapp -papp inboxbrain -e "UPDATE email_queue SET status='pending', attempts=0 WHERE status='error';"
  ```
