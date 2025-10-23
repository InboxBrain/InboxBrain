#!/usr/bin/env bash
set -euo pipefail

ROLE="${APP_ROLE:-combo}"

# Wait for MySQL to be ready
echo "Waiting for MySQL..."
python - <<'PY'
import os, time
from sqlalchemy import create_engine, text
dsn = os.getenv("DB_DSN")
for i in range(60):
    try:
        eng = create_engine(dsn, pool_pre_ping=True)
        with eng.connect() as cx:
            cx.execute(text("SELECT 1"))
        print("MySQL is ready.")
        break
    except Exception as e:
        print("Waiting...", e)
        time.sleep(2)
else:
    raise SystemExit("MySQL not ready after timeout")
PY

# Pick role
if [ "$ROLE" = "ingestor" ]; then
  exec python run_ingestor_imap.py
elif [ "$ROLE" = "worker" ]; then
  exec python run_worker_ai.py
elif [ "$ROLE" = "api" ]; then
  exec uvicorn api:app --host 0.0.0.0 --port 8000
else
  # combo: run all (simple dev mode)
  uvicorn api:app --host 0.0.0.0 --port 8000 &
  while true; do
     python run_ingestor_imap.py || true
     sleep 120
     python run_worker_ai.py || true
     sleep 20
  done
fi
