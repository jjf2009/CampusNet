# CampusNet technical project explanation

## 1. Executive summary

CampusNet is a local network-operations prototype for observing campus authentication activity. It deliberately separates authentication from monitoring:

1. FreeRADIUS makes the authentication decision.
2. FreeRADIUS emits a restricted structured event.
3. A FastAPI worker validates and ingests the event.
4. SQLAlchemy persists it in SQLite.
5. A Next.js dashboard reads the API and presents operational status.

This is an observability and administration layer, not a replacement for an access point, RADIUS server, identity provider, directory, DHCP service, firewall, or network controller.

## 2. End-to-end data flow

```text
Supplicant / student device
        │ 802.1X and EAP in a real deployment
        ▼
Authenticator: AP or switch
        │ RADIUS Access-Request over UDP
        ▼
FreeRADIUS
        │ Access-Accept or Access-Reject
        ├── authentication policy and identity lookup
        └── safe structured post-auth event
                    │ JSON Lines file
                    ▼
         CampusNet ingestion worker
                    │ parse, validate, deduplicate
                    ▼
              SQLite event store
                    │ HTTP JSON API
                    ▼
              Next.js admin dashboard
```

The event path is intentionally one-way from the authentication server to the dashboard. The dashboard does not make authentication decisions and does not receive passwords.

## 3. Major components

### FreeRADIUS

FreeRADIUS is an open-source RADIUS server. RADIUS is a protocol used by network access devices to ask an authentication server whether a user or device should receive network access.

Important concepts:

- **NAS (Network Access Server):** the access point, switch, or controller requesting authentication.
- **Access-Request:** the NAS request containing identity and authentication attributes.
- **Access-Accept:** the server accepts the request and may return policy attributes such as VLAN information.
- **Access-Reject:** the server denies the request.
- **shared secret:** a server/NAS trust secret used to protect and authenticate RADIUS packets; it must never enter application logs.
- **post-auth:** the FreeRADIUS processing section that runs after an authentication decision and is the appropriate place to emit a result event.
- **linelog:** a FreeRADIUS module capable of writing selected attributes to a dedicated log format.

CampusNet must use a dedicated safe event logger, not parse interactive `radiusd -X` debug output. The application-side consumer is implemented; the host integration procedure is approval-gated in `RADIUS-INTEGRATION.md`.

### FastAPI backend

FastAPI is the Python HTTP framework exposing the application contract:

- `/health` checks application/database health;
- `/api/events` provides paginated, filtered event records;
- `/api/stats` calculates totals and acceptance rate;
- `/api/radius/status` reports the independently checked host service state;
- `/api/system/overview` combines operational summary data; and
- `/api/users` reports usernames observed in events, not a complete student directory.

Pydantic response models define response shapes. This gives the frontend a stable contract and prevents accidental exposure of arbitrary database fields.

### Ingestion worker

The worker polls a JSON Lines file without blocking the FastAPI request path. Each line resembles:

```json
{"event_id":"...","timestamp":"...","username":"...","result":"accept"}
```

The parser uses an allow-list of safe fields. It rejects malformed JSON, missing usernames, invalid results, and invalid timestamps. It derives a stable hash when an event has no explicit ID.

The tailer tracks a cursor, waits for incomplete final lines, detects truncation/log rotation, and ignores duplicate event IDs. This is a lightweight local implementation; production would normally use a durable log pipeline or message broker with stronger delivery and retention guarantees.

### SQLAlchemy and SQLite

SQLAlchemy is the ORM and database abstraction layer. The `AuthenticationEvent` table stores:

- unique event identifier;
- UTC event timestamp;
- normalized username;
- `accept` or `reject` result;
- optional NAS, station, and authentication-method metadata;
- source and creation timestamps.

Indexes support common operations on event time, username, result, and unique event ID. SQLite is appropriate for a laptop demonstration; PostgreSQL would be more suitable for production concurrency, availability, backup, and operational scale.

### Next.js dashboard

Next.js provides the React-based frontend. The dashboard uses typed fetch helpers to call the backend and renders:

- API, RADIUS, and ingestion status;
- total, accepted, rejected, and acceptance-rate metrics;
- searchable and result-filtered recent events;
- loading, empty, disconnected, and error states; and
- periodic refresh with a manual refresh action.

The dashboard is read-only and contains no administrative credentials or server-side secrets.

## 4. Security model

The prototype follows least privilege and data minimization:

- only fictional local credentials are used;
- no Google password is collected or validated by CampusNet;
- passwords, RADIUS shared secrets, private keys, and debug traces are excluded from event data;
- the backend and frontend bind to localhost by default;
- CORS is restricted to the configured local frontend origin;
- database access uses SQLAlchemy query methods rather than interpolated SQL;
- the RADIUS service is checked using a fixed configured service name, never user-controlled shell input; and
- system configuration changes are separated from application code and require backup, approval, and rollback instructions.

For production, IT would also need threat modeling, TLS and certificate management, dashboard access control, audit logging, retention limits, privacy review, vulnerability management, and incident response procedures.

## 5. Authentication terminology to research

### 802.1X

802.1X is port-based network access control. It defines how a supplicant, authenticator, and authentication server cooperate before network access is granted. The access point or switch is the authenticator; it usually forwards authentication to RADIUS.

### EAP

Extensible Authentication Protocol is a framework for authentication methods. EAP itself is not one credential method. Common enterprise choices include EAP-TLS, PEAP, and EAP-TTLS.

### EAP-TLS

EAP-TLS uses client and server certificates. It is a strong production direction because it can avoid password-based authentication, but it requires certificate issuance, renewal, revocation, trusted roots, device lifecycle management, and help-desk processes.

### PEAP / MSCHAPv2

PEAP creates a protected tunnel and commonly carries MSCHAPv2 inside it. It is widely supported but has password, phishing, legacy compatibility, and identity-provider trade-offs. It must not be assumed compatible with Google Workspace without institutional verification.

### VLAN assignment

An accepted RADIUS response can include policy attributes that tell network infrastructure which VLAN or role to apply. RADIUS does not by itself provide DHCP, DNS, routing, firewalling, or internet service. Those systems must be designed together.

### RADIUS accounting and observability

Authentication tells us whether access was accepted. Accounting records can describe session start, interim updates, and session stop. A mature monitoring design may correlate authentication events with accounting, device inventory, controller telemetry, and alerting while respecting privacy and retention rules.

## 6. Reliability and operations terminology

- **Idempotency:** processing the same event repeatedly produces one stored result rather than duplicates.
- **Cursor/offset:** the reader position used to resume a file after restart.
- **Log rotation:** replacing or truncating a log while a service continues running; readers must detect the change.
- **Backpressure:** controlling ingestion when the producer is faster than the consumer.
- **Health check:** whether a component is functioning, not merely whether its process exists.
- **Liveness:** whether a process is running; **readiness:** whether it can perform useful work.
- **High availability:** multiple service instances and failover so one host failure does not stop authentication or monitoring.
- **Retention policy:** how long events are stored and when they are deleted for privacy, cost, and compliance reasons.
- **MTTR / RTO / RPO:** recovery time, service restoration target, and acceptable data-loss window.

## 7. Production architecture questions for IT

Before deployment, the project must answer:

1. Which identity source is institution-approved: directory, identity provider, Secure LDAP, certificate authority, or another system?
2. Is EAP-TLS required, and who owns certificate enrollment and revocation?
3. Which access points, switches, controllers, and RADIUS source interfaces are in scope?
4. What are the VLAN, DHCP, DNS, firewall, guest, staff, student, and quarantine policies?
5. What data may be retained, for how long, and who may view it?
6. How will RADIUS and the dashboard be monitored, backed up, upgraded, and recovered?
7. What is the pilot scope, rollback plan, support process, and approval authority?

These are discovery questions. The prototype does not invent network topology, IP ranges, VLAN IDs, controller models, licensing, or institutional policy.

## 8. How to present the project seriously

Lead with this boundary:

> This is a controlled local proof of the authentication-event observability layer. It preserves FreeRADIUS as the decision point and does not claim production Wi-Fi integration.

Then show evidence:

- automated parser and ingestion tests;
- exact API contracts and health separation;
- safe-field allow-list and duplicate protection;
- localhost security defaults;
- explicit rollback and approval controls for system changes; and
- a roadmap that identifies institutional decisions rather than guessing them.

That combination demonstrates engineering discipline: a working vertical slice, a clear threat boundary, and an honest production gap analysis.
