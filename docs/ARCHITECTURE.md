# CampusNet architecture

## Production authentication flow

```text
Student device / supplicant
        |
        | 802.1X / EAP
        v
Campus access point / authenticator
        |
        | RADIUS Access-Request
        v
Central FreeRADIUS server
        |
        | Authentication decision
        v
Identity source / policy
        |
        | Access-Accept or Access-Reject
        v
Access point enforces network access
        |
        +---- VLAN assignment (if configured)
        +---- DHCP / DNS
        +---- Routing / firewall policy

FreeRADIUS authentication event
        |
        v
Structured event log  (JSON Lines, safe fields only)
        |
        v
FastAPI ingestion worker  (tail + cursor, idempotent)
        |
        v
SQLite (prototype) / PostgreSQL (future)
        |
        v
Next.js admin dashboard
```

## Roles

- **Supplicant** — the student's device (laptop/phone) running an 802.1X
  client. Sends EAP credentials; never talks to CampusNet's web app.
- **Authenticator** — the campus access point or switch. Relays EAP between
  the supplicant and RADIUS and enforces the access decision (port/VLAN).
  In production these are Cisco APs/controllers; in this prototype the
  authenticator is simulated by `radtest` (and, optionally, a laptop
  `hostapd` AP in Phase D).
- **Authentication server** — FreeRADIUS 3.2.8 on the host. Makes the
  accept/reject decision. This is real and locally verified via PAP.
- **Identity source** — local demo users in the prototype
  (`student01@gec.edu.in`). In production, an institution-approved
  directory / IdP (see PRODUCTION-ROADMAP). CampusNet never collects Google
  passwords and is not a student directory.
- **VLAN & network policy** — applied by the network infrastructure
  (authenticator + controller), not by RADIUS alone.
- **DHCP / DNS / routing / firewall** — required for usable access after a
  successful authentication; out of scope for the prototype.
- **Roaming** — depends on AP/controller configuration and supported 802.1X
  roaming; a discovery item.
- **Monitoring** — the CampusNet event pipeline and dashboard (this repo).

## Prototype data path (what is real here)

1. FreeRADIUS writes one JSON line per authentication outcome to a dedicated
   `linelog` file (`/var/log/campusnet/radius-events.jsonl`). Only safe
   fields are written — never `User-Password` or shared secrets.
2. The FastAPI ingestion worker tails that file on a bounded poll interval,
   parses and sanitizes each line, and persists unseen events to SQLite. A
   byte-offset cursor makes restarts safe; `event_id` makes replays
   idempotent.
3. The API exposes read-only endpoints (events, stats, RADIUS status, system
   overview, users). CORS is restricted to the local frontend origin.
4. The Next.js dashboard polls the API every ~7s and renders status,
   metrics, a data-derived activity chart, and a filterable event table.

## Component map

| Layer      | Technology            | Location                         |
|------------|-----------------------|----------------------------------|
| AuthN      | FreeRADIUS 3.2.8      | host `/etc/raddb` (system)       |
| Event log  | `linelog` → JSONL    | `/var/log/campusnet/…`           |
| Ingestion  | async worker         | `backend/app/workers/`           |
| Parsing    | tolerant parser      | `backend/app/services/parser.py` |
| API        | FastAPI + SQLAlchemy | `backend/app/api/`               |
| Store      | SQLite               | `backend/campusnet.db`           |
| Dashboard  | Next.js + Tailwind   | `frontend/app/`                  |

Boundary note: the RADIUS configuration lives in the host system, not this
repository. The repo changes it only through the approval-gated scripts
documented in `RADIUS-INTEGRATION.md`.
