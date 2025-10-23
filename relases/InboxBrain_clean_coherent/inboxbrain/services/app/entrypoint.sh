#!/usr/bin/env bash
set -e

INGEST_SLEEP="${INGEST_SLEEP:-60}"
WORKER_SLEEP="${WORKER_SLEEP:-30}"
ENABLE_IMAP_IDLE="${ENABLE_IMAP_IDLE:-false}"

# Start API
uvicorn api:app --host 0.0.0.0 --port 8000 &

if [ "$ENABLE_IMAP_IDLE" = "true" ]; then
  echo "Starting IMAP IDLE ingestor..."
  python run_ingestor_idle.py &
  while true; do
    python run_worker_ai.py || true
    sleep "$WORKER_SLEEP"
  done
else
  echo "Starting polling ingestor/worker loop..."
  while true; do
    python run_ingestor_imap.py || true
    sleep "$INGEST_SLEEP"
    python run_worker_ai.py || true
    sleep "$WORKER_SLEEP"
  done
fi
