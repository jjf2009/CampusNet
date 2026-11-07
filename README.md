# CampusNet

A localhost prototype of a campus Wi-Fi authentication and monitoring platform:
**FreeRADIUS → structured event log → FastAPI ingestion worker → SQLite → Next.js
dashboard**. Authentication decisions are made by a real, locally installed
FreeRADIUS server — the app is an observability layer on top, not a replacement.

## Status

Verified working end-to-end on the development host:

- Real FreeRADIUS authentication (PAP via `radtest`, and **WPA2-Enterprise /
  802.1X PEAP-MSCHAPv2 from a phone**) → both `Access-Accept` and `Access-Reject`.
- Safe structured events ingested into SQLite (no passwords or secrets stored).
- FastAPI endpoints serve persisted data; Next.js dashboard renders it with
  loading / empty / error / disconnected states.
- A phone joining the `CampusNet-Demo` SSID authenticates against FreeRADIUS and
  appears live on the dashboard (Phase D, auth-only mode).

Not production: single local demo user, SQLite, unauthenticated localhost
dashboard. Google Workspace, Cisco controllers, VLANs, and HA are documented
future work — see `docs/PRODUCTION-ROADMAP.md`.

## Architecture

```
phone / supplicant --802.1X/EAP--> laptop AP (hostapd) --RADIUS--> FreeRADIUS
                                                                       |
                                              linelog JSONL  <---------+
                                                   |
                           FastAPI ingestion worker (tail + cursor, idempotent)
                                                   |
                                                SQLite
                                                   |
                                         FastAPI read-only API
                                                   |
                                          Next.js dashboard
```

Full diagram and role descriptions: `docs/ARCHITECTURE.md`.

## Local setup

```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
# Frontend (second terminal)
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open the dashboard at <http://127.0.0.1:3000>, API docs at
<http://127.0.0.1:8000/docs>, health at <http://127.0.0.1:8000/health>.

To rehearse the UI without touching FreeRADIUS, point the backend at the
labelled fixture (simulated input, clearly not a live transaction):

```bash
cd backend
rm -f data/ingestion.cursor
RADIUS_EVENT_LOG=./fixtures/events.jsonl uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Configuration (backend `.env`)

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./campusnet.db` | Event store. |
| `RADIUS_EVENT_LOG` | `./data/radius-events.jsonl` | Log the ingestion worker tails. Live path: `/var/log/campusnet/radius-events.jsonl`. |
| `INGESTION_CURSOR_PATH` | `./data/ingestion.cursor` | App-local cursor (the RADIUS log dir is read-only for the backend). |
| `RADIUS_SERVICE_NAME` | `radiusd` | systemd unit used for the RADIUS health check. |
| `POLL_INTERVAL_SECONDS` | `2` | Ingestion poll interval. |
| `FRONTEND_ORIGIN` | `http://127.0.0.1:3000` | Allowed CORS origin. |

Frontend `.env.local`: `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000`.

## API

- `GET /health` — API + DB + ingestion state (RADIUS reported separately).
- `GET /api/events` — recent events; filters `result`, `username`, `since`, `until`; `limit`/`offset`.
- `GET /api/events/{event_id}` — single event.
- `GET /api/stats` — totals, acceptance rate, windowed counts.
- `GET /api/radius/status` — `systemctl is-active` of the RADIUS service.
- `GET /api/system/overview` — combined API/DB/RADIUS/ingestion + latest event.
- `GET /api/users` — distinct usernames seen in events (not a directory).

## Tests and build

```bash
cd backend && python -m pytest        # parser, tailer, ingestion dedup, API, CORS
cd frontend && npm run build          # production build (npm run lint = tsc --noEmit)
```

## Scripts (`scripts/`)

| Script | What it does |
|---|---|
| `check-radius.sh` | Local RADIUS service health check. |
| `test-event-log.sh` | Verify the event pipeline with valid/invalid `radtest` (no secrets printed). |
| `configure-radius-campusnet.sh` | Approval-gated: back up `/etc/raddb`, install the two `linelog` instances + hooks, SELinux label, validate with `radiusd -XC`. |
| `fix-campusnet-accept-hook.sh` | Repair a live config where the accept hook was misplaced outside `post-auth {}`. Backs up, validates, auto-restores on failure. |
| `start-campusnet-ap-local.sh` / `stop-campusnet-ap-local.sh` | **Auth-only** WPA2-Enterprise demo AP (no internet/NAT/firewall forwarding). Recommended for the live demo. |
| `start-campusnet-ap.sh` / `stop-campusnet-ap.sh` | Full AP with USB-tether upstream + NAT (client also gets internet). |

RADIUS integration and the live 802.1X demo are documented in
`docs/RADIUS-INTEGRATION.md` and `docs/DEMO-GUIDE.md` (§8).

## Security

- No passwords, RADIUS shared secrets, keys, or debug output are stored, logged,
  or returned. Secrets live only in root-owned env files (mode 600), never in Git.
- API and dashboard bind to `127.0.0.1` by default. Exposing the portal to a
  connected phone (`npm run dev:ap`) is an explicit opt-in on the isolated AP
  network only.
- System changes to `/etc/raddb`, Wi-Fi, or firewall state are approval-gated,
  backed up, and reversible. SELinux stays enforcing.

## Troubleshooting

See `docs/DEMO-GUIDE.md` §6. Common ones: ingestion `waiting` → check
`RADIUS_EVENT_LOG` exists and is readable; events missing after auth → check the
JSONL path/permissions and SELinux label on `/var/log/campusnet`; phone "no IP"
→ the auth-only AP needs the DHCP firewall allowance (handled by the script).
