# CampusNet

CampusNet is a local network-operations prototype that captures safe FreeRADIUS authentication outcomes, persists them in SQLite, and presents them in a Next.js dashboard.

## Local setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open http://127.0.0.1:3000. The dashboard reads only from the backend API. To demonstrate the UI without changing FreeRADIUS, point `RADIUS_EVENT_LOG` at `backend/fixtures/events.jsonl`.

## Verification

```bash
cd backend
python -m pytest
```

The API is documented at http://127.0.0.1:8000/docs. FreeRADIUS integration is intentionally approval-gated; see `docs/RADIUS-INTEGRATION.md`.

## Scope

Local FreeRADIUS PAP authentication and event monitoring are supported. Google Workspace, Cisco production integration, and WPA2-Enterprise access-point integration are not claimed as complete. See `docs/ARCHITECTURE.md` and `docs/PRODUCTION-ROADMAP.md`.
