# Scaling & Performance

- **Ingestor**: mantieni poll >= 60–120s; o passa a **IMAP IDLE** per near-realtime e carico minimo.
- **Worker**: aumenta frequenza se vuoi svuotare coda più rapidamente (non impatta IMAP).
- **Batches**: riduci `FIRST_RUN_BATCH` per caselle molto grandi (50-100).
- **Separazione ruoli**: esegui container separati per API/ingestor/worker.
- **Monitoring**: esporta metriche (es. tabelle derivate sul DB) e collega a Metabase.
