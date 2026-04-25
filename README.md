# OpenGRC

This repository now includes a lightweight local OpenGRC API implementation that matches the workflow export (`OpenGRC FCC Control Set Bootstrap - Production Ready.json`).

## Run the API

```bash
python3 api/server.py
```

By default, the server listens on `http://0.0.0.0:8000`.

Optional environment variables:

- `OPENGRC_API_HOST` (default: `0.0.0.0`)
- `OPENGRC_API_PORT` (default: `8000`)
- `OPENGRC_API_TOKEN` (default: the token embedded in the n8n workflow)

## Supported endpoints

### Health

- `GET /health`

### Create resources (Bearer token required)

- `POST /api/standards`
- `POST /api/programs`
- `POST /api/controls`
- `POST /api/implementations`

### List resources

- `GET /api/standards`
- `GET /api/programs`
- `GET /api/controls`
- `GET /api/implementations`

## Quick smoke test

```bash
TOKEN='3|vln7XSv3QEYNJXxq7jfsLHGUICreFG6RtzF5E6Og86fe40dd'
BASE='http://127.0.0.1:8000'

curl -s "$BASE/health"

STD_ID=$(curl -s -X POST "$BASE/api/standards" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"code":"FCC-ZTR","title":"FCC Standard"}' | python3 -c 'import sys, json; print(json.load(sys.stdin)["data"]["id"])')

PRG_ID=$(curl -s -X POST "$BASE/api/programs" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"code":"FCC-ZTR-PROGRAM","title":"FCC Program"}' | python3 -c 'import sys, json; print(json.load(sys.stdin)["data"]["id"])')

CTL_ID=$(curl -s -X POST "$BASE/api/controls" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"code\":\"FCC-ZTR-001\",\"identifier\":\"FCC-ZTR-001\",\"title\":\"Control\",\"description\":\"Control Description\",\"status\":\"active\",\"standard_id\":$STD_ID,\"program_id\":$PRG_ID}" | python3 -c 'import sys, json; print(json.load(sys.stdin)["data"]["id"])')

curl -s -X POST "$BASE/api/implementations" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"code\":\"FCC-ZTR-001-IMPL\",\"identifier\":\"FCC-ZTR-001-IMPL\",\"title\":\"Implementation\",\"description\":\"Implementation Description\",\"status\":\"implemented\",\"control_id\":$CTL_ID,\"standard_id\":$STD_ID,\"program_id\":$PRG_ID}"
```

You can set your n8n workflow `base_url` to `http://<host>:8000` and keep using the same payloads.
