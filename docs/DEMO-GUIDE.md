# CampusNet full demonstration guide

This guide is designed for a 3–5 minute presentation to the IT department. It separates currently implemented behavior from work requiring FreeRADIUS administrator approval or production infrastructure.

## 1. What the demonstration proves

The demonstration proves that CampusNet can:

- receive safe, structured authentication outcomes;
- validate and normalize event records without storing passwords or RADIUS secrets;
- persist events in SQLite with duplicate protection;
- expose persisted data through a typed FastAPI API; and
- display API data in a responsive Next.js operations dashboard.

With Phase D (§8) run on this host it also demonstrates a real **WPA2-Enterprise / 802.1X**
login: a phone authenticates against the host FreeRADIUS over PEAP-MSCHAPv2 and the outcome
appears on the dashboard. A `radtest` alone is only a RADIUS protocol test and is not proof of
802.1X — the phone connection is. It does **not** claim a production access point, Cisco
controller, or Google Workspace integration; those remain future work.

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
| Event log stays empty after auth | SELinux may be denying `radiusd` the write. Check `sudo ausearch -m avc -ts recent`; confirm the `radiusd_log_t` label on `/var/log/campusnet` from the configure script. |
| Reject events missing, accepts fine | The reject hook (`Post-Auth-Type REJECT`) is not installed; re-run the fixed configure script against a clean `/etc/raddb` backup. |
| Phone cannot associate (PEAP) | Confirm PEAP server certs exist in `/etc/raddb/certs` (`sudo /etc/raddb/certs/bootstrap`), `default_eap_type = peap`, and the phone CA set to "Do not validate". |
| `radtest` is rejected unexpectedly | Verify the local demo user and PAP configuration with the RADIUS administrator; do not expose debug output in the dashboard. |
| Port already in use | Stop the existing local process or choose an explicitly documented local development port. |

## 7. Claims boundary

Currently demonstrated: local application, SQLite persistence, safe event parsing, API contracts, dashboard rendering, and automated parser tests.

Live when §8 has been run successfully on this host: a real WPA2-Enterprise/802.1X PEAP-MSCHAPv2
authentication from a separate phone, decided by FreeRADIUS and recorded as a dashboard event.
Claim this only after a phone has actually connected over `CampusNet-Demo`; otherwise it remains
a local protocol demo (`radtest`) plus the observability layer.

Approval-gated or future: editing `/etc/raddb`, live FreeRADIUS `linelog` activation, protected log permissions, host service reload, installing/configuring `hostapd`, changing Wi-Fi/forwarding/firewall state, Google Workspace integration, Cisco integration, VLAN assignment, production monitoring, and deployment beyond localhost. The guarded AP scripts and rollback procedure are in `scripts/`.

## 8. Live WPA2-Enterprise (802.1X) demonstration

This is the Phase D demo: a separate phone authenticates against the host FreeRADIUS over
real 802.1X, and the resulting Accept/Reject appears on the dashboard. The laptop Wi-Fi
adapter is the isolated downstream AP.

A `radtest` (§4) proves only the RADIUS protocol and the event pipeline. Only a phone
connecting over `CampusNet-Demo` with an enterprise profile proves 802.1X. State that
distinction in the presentation.

**Two modes — pick one:**

- **Auth-only (recommended, §8.4):** the phone authenticates and appears on the dashboard
  but gets no internet. No USB tether, no NAT, no firewall changes — simplest and safest,
  and it is all the demo needs. The 802.1X exchange completes during association, before
  internet would matter. Uses `scripts/start-campusnet-ap-local.sh`.
- **With internet (§8.2):** a USB-tethered phone provides upstream so the connecting device
  also gets internet via NAT. More moving parts (needs a second phone for the tether). Uses
  `scripts/start-campusnet-ap.sh`.

§8.1 (RADIUS integration) applies to both. The common chip check: the laptop's Realtek
adapter must actually run an AP — bring the AP up once before demo day and confirm
`AP-ENABLED` in the hostapd log; if the driver errors, use a known-good USB Wi-Fi adapter.

### 8.1 One-time RADIUS integration (administrator, approval-gated)

Apply the dedicated event logger and enable PEAP (see `docs/RADIUS-INTEGRATION.md`). The
configure script backs up `/etc/raddb`, installs two safe `linelog` instances
(Accept and Reject paths), labels the event directory for SELinux (`radiusd_log_t`), and
validates with `radiusd -XC` without restarting:

```bash
sudo env CONFIRM_CAMPUSNET_RADIUS=YES APP_USER="$USER" scripts/configure-radius-campusnet.sh
sudo systemctl restart radiusd && systemctl is-active radiusd
```

Point `backend/.env` at the host log: `RADIUS_EVENT_LOG=/var/log/campusnet/radius-events.jsonl`.
SELinux must stay enforcing; `semanage` (`policycoreutils-python-utils`) is required by the script.

### 8.2 Start the access point

Install the AP package once (if absent):

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

### 8.3 Connect the test phone

On the second phone, select SSID `CampusNet-Demo` and enter:

- Security: **WPA2-Enterprise** (802.1X)
- EAP method: **PEAP**
- Phase-2 authentication: **MSCHAPV2**
- Identity: `student01@gec.edu.in`
- Password: the fictional local demo password
- CA certificate: **Do not validate** (the host uses a self-signed demo certificate; Android 11+
  requires this toggle). This is acceptable for a local demo only. Production must use a trusted
  CA and real certificate validation — never bypass it.

On `Access-Accept` the phone joins; the ingestion worker (polling every few seconds) adds the
event with `auth_method=eap`, the phone MAC as calling-station, and the AP/SSID as
called-station. Enter a wrong password once to show an `Access-Reject` event. No manual refresh
is needed — the dashboard polls, or use its refresh action.

After testing both accepted and rejected credentials, restore the laptop:

```bash
sudo scripts/stop-campusnet-ap.sh
nmcli device status
```

If the AP script stops during startup, it attempts the same rollback automatically. Never bridge this demo into a college or public network.

### 8.4 Auth-only mode (recommended — no internet)

Simpler than §8.2: the phone authenticates and shows on the dashboard, with no USB tether,
no NAT, and no firewall changes. §8.1 (RADIUS integration) must already be applied, and
`backend/.env` must point at the host log.

Create the local root-owned env file (mode `600`) holding only the RADIUS shared secret —
`UPSTREAM_IFACE` is not needed in this mode:

```bash
sudo install -m 600 /dev/null /etc/campusnet-ap.env
sudoedit /etc/campusnet-ap.env   # set WIFI_IFACE, AP_SSID, AP_CHANNEL, RADIUS_SHARED_SECRET
```

Chip feasibility check (do once before demo day; fully reversible):

```bash
sudo env CONFIRM_CAMPUSNET_AP=YES bash scripts/start-campusnet-ap-local.sh
sudo grep -i 'AP-ENABLED\|interface state' /run/campusnet-ap/hostapd.log   # want AP-ENABLED
sudo bash scripts/stop-campusnet-ap-local.sh
```

Demo run (backend + frontend already up, dashboard open):

```bash
sudo env CONFIRM_CAMPUSNET_AP=YES bash scripts/start-campusnet-ap-local.sh
```

Connect the test phone exactly as in §8.3 (WPA2-Enterprise / PEAP / MSCHAPV2 / identity
`student01@gec.edu.in` / CA "Do not validate"). The dashboard shows a live `Access-Accept`
within a few seconds; a wrong password shows `Access-Reject`. The phone will report
"connected, no internet" — that is expected and does not affect the authentication demo.

Restore the laptop Wi-Fi afterwards:

```bash
sudo bash scripts/stop-campusnet-ap-local.sh
```

If `hostapd` or `dnsmasq` dies immediately, SELinux may be denying access to
`/run/campusnet-ap/`; check `sudo ausearch -m avc -ts recent | tail` and relabel rather than
disabling SELinux.
