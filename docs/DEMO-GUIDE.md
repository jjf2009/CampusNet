# CampusNet full demonstration guide

This guide is designed for a 3–5 minute presentation to the IT department. It separates currently implemented behavior from work requiring FreeRADIUS administrator approval or production infrastructure.

## 1. What the demonstration proves

The demonstration proves that CampusNet can:

- receive safe, structured authentication outcomes;
- validate and normalize event records without storing passwords or RADIUS secrets;
- persist events in SQLite with duplicate protection;
- expose persisted data through a typed FastAPI API; and
- display API data in a responsive Next.js operations dashboard.

It does not claim that a production access point, Cisco controller, Google Workspace, or WPA2-Enterprise client is connected. A `radtest` is a RADIUS protocol test; it is not by itself proof of a complete 802.1X Wi-Fi deployment.

## 2. Pre-demo safety checklist

- Use only the fictional local demo account.
- Keep all services bound to `127.0.0.1`.
- Do not show `/etc/raddb` secrets, private keys, `radiusd -X` output, or passwords on screen.
- Do not modify or reload FreeRADIUS during a presentation.
- Explain that any production RADIUS client, identity integration, VLAN policy, or firewall change requires IT approval.

## 3. Prepare the application

From the repository root:

```bash
cd backend
source .venv/bin/activate
python -m pytest
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd frontend
npm run dev
```

Open:

- Dashboard: <http://127.0.0.1:3000>
- API documentation: <http://127.0.0.1:8000/docs>
- Health endpoint: <http://127.0.0.1:8000/health>

The backend reads `RADIUS_EVENT_LOG` from `backend/.env`. The intended live path is a dedicated FreeRADIUS JSON Lines log. For a safe UI rehearsal, use the supplied fictional fixture:

```bash
cd backend
rm -f fixtures/events.jsonl.cursor
RADIUS_EVENT_LOG=./fixtures/events.jsonl \
  uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The fixture is simulated input for rehearsal. It is not evidence of a live RADIUS transaction.

## 4. Presentation sequence

### Opening: explain the architecture

Say:

> CampusNet does not replace FreeRADIUS. FreeRADIUS remains the authentication authority. CampusNet consumes a restricted event stream, stores operational metadata, and gives administrators a local visibility layer.

Point to the dashboard status cards:

- API: whether FastAPI is reachable;
- RADIUS: the separately checked host service state;
- ingestion: whether the event log is available to the worker.

This separation is important: a healthy API does not automatically mean that RADIUS is healthy.

### Successful authentication

If the local demo user has been configured and the approved RADIUS integration is active, run a fictional valid request:

```bash
radtest 'student01@gec.edu.in' '<fictional-demo-password>' 127.0.0.1 0 '<local-radius-shared-secret>'
```

Replace `<fictional-demo-password>` with the local fictional password already configured by the administrator. Do not place real institutional credentials in this command.

Expected result:

```text
Access-Accept
```

Refresh the dashboard and show that one accepted event appears. Point out the timestamp, normalized username, result badge, and available NAS/AP/client metadata.

### Rejected authentication

Run the same test with an intentionally incorrect fictional password:

```bash
radtest 'student01@gec.edu.in' '<intentionally-wrong-demo-password>' 127.0.0.1 0 '<local-radius-shared-secret>'
```

Expected result:

```text
Access-Reject
```

Refresh the dashboard and show the rejected event and updated counters. Explain that rejection is an expected authentication outcome, not necessarily an application failure.

### API verification

Use Swagger or these read-only commands:

```bash
curl -s http://127.0.0.1:8000/health
curl -s 'http://127.0.0.1:8000/api/events?limit=10'
curl -s http://127.0.0.1:8000/api/stats
curl -s http://127.0.0.1:8000/api/radius/status
curl -s http://127.0.0.1:8000/api/system/overview
```

Demonstrate filtering:

```bash
curl -s 'http://127.0.0.1:8000/api/events?result=reject&username=student01'
```

Explain that the dashboard displays values returned from persisted backend data rather than fake browser-side numbers.

## 5. Closing explanation

Use this closing statement:

> The local authentication decision is made by FreeRADIUS. CampusNet records only safe operational fields, protects against duplicate ingestion, persists the event, and presents it to an administrator. The next production decisions are institutional identity integration, certificate strategy, high availability, network-device configuration, privacy retention, and IT approval.

## 6. Troubleshooting

| Symptom | Check |
|---|---|
| Dashboard says API unavailable | Confirm Uvicorn is running on port 8000 and `NEXT_PUBLIC_API_URL` is correct. |
| Ingestion says waiting | Confirm `RADIUS_EVENT_LOG` exists and is readable by the backend user. |
| RADIUS is unknown | The API could not verify the configured `systemctl` service state; check the service manually. |
| Events do not appear | Check the JSON Lines path, file permissions, timestamp, username, and `result` value. |
| `radtest` is rejected unexpectedly | Verify the local demo user and PAP configuration with the RADIUS administrator; do not expose debug output in the dashboard. |
| Port already in use | Stop the existing local process or choose an explicitly documented local development port. |

## 7. Claims boundary

Currently demonstrated: local application, SQLite persistence, safe event parsing, API contracts, dashboard rendering, and automated parser tests.

Approval-gated or future: editing `/etc/raddb`, live FreeRADIUS `linelog` activation, protected log permissions, host service reload, installing/configuring `hostapd`, changing Wi-Fi/forwarding/firewall state, WPA2-Enterprise access-point testing, Google Workspace integration, Cisco integration, VLAN assignment, production monitoring, and deployment beyond localhost. The guarded AP scripts and rollback procedure are in `scripts/`.

## 8. Laptop hotspot procedure

This procedure uses the phone connected by USB as the upstream internet connection and the laptop Wi-Fi adapter as the isolated downstream AP.

Install the missing AP package once:

```bash
sudo dnf install hostapd
```

Connect USB tethering, then identify the upstream interface:

```bash
nmcli device status
ip route get 1.1.1.1
```

Create the local root-owned configuration from the example, set its mode to `600`, and replace only the placeholder values locally:

```bash
sudo install -m 600 scripts/campusnet-ap.conf.example /etc/campusnet-ap.env
sudoedit /etc/campusnet-ap.env
```

Set `UPSTREAM_IFACE` to the USB-tether interface and set the RADIUS shared secret without committing or displaying it. Then start the guarded AP:

```bash
sudo env CONFIRM_CAMPUSNET_AP=YES \
  CAMPUSNET_AP_ENV=/etc/campusnet-ap.env \
  scripts/start-campusnet-ap.sh
```

On the friend’s phone, select `CampusNet-Demo`, choose WPA2-Enterprise/802.1X, use the fictional demo username and local demo password, and select the institution-approved CA validation option. The exact EAP method and CA trust behavior depend on the FreeRADIUS EAP configuration and phone OS; do not bypass certificate validation in a production design.

After testing both accepted and rejected credentials, restore the laptop:

```bash
sudo scripts/stop-campusnet-ap.sh
nmcli device status
```

If the AP script stops during startup, it attempts the same rollback automatically. Never bridge this demo into a college or public network.
