# API

Auth: header `x-api-token: <API_TOKEN>`

## `GET /health`
Risponde `{"ok": true}` se l'app è up e il DB risponde.

## `GET /emails?limit=50&intent=<intent>`
Ritorna lista con metadati principali e (se disponibili) `intent` e `confidence` da `email_ai`.

Esempio:
```bash
curl -H "x-api-token: changeme" "http://localhost:8000/emails?limit=20"
```
