# CampusNet --- Coding Agent Build Specification

> **Mission:** Build a credible, working, laptop-demonstrable prototype
> of CampusNet: a centralized campus Wi-Fi authentication and monitoring
> platform.
>
> **Primary objective:** Deliver a functional end-to-end MVP, not a
> static mockup. The system must use the locally installed FreeRADIUS
> server for real authentication decisions, expose safe authentication
> events through FastAPI, persist them in SQLite, and display them in a
> polished Next.js admin dashboard.

------------------------------------------------------------------------

## 1. Project context

CampusNet is a proposed campus network access platform for a college
environment.

The intended production experience:

-   A student connects to a campus Wi-Fi network.
-   The student's institution-managed identity is used to authenticate.
-   Campus access points forward 802.1X authentication requests to a
    central RADIUS server.
-   RADIUS makes the authentication decision.
-   The network infrastructure grants or denies access and may assign
    the student to an appropriate VLAN.
-   Administrators monitor authentication activity, service health, and
    network access.

The current prototype is being developed on a Fedora laptop without
access to the college's production network infrastructure. It must
therefore be demonstrable locally, with clear boundaries between working
functionality and future production integrations.

### Current verified environment

-   OS: Fedora 44 Workstation.
-   Project directory: `~/Desktop/Projects/CampusNet`.
-   FreeRADIUS: version 3.2.8, installed from Fedora packages.
-   FreeRADIUS configuration directory: `/etc/raddb/`.
-   FreeRADIUS certificate directory: `/etc/raddb/certs/`.
-   FreeRADIUS is able to start and prints `Ready to process requests`.
-   A fictional test account has been configured:
    -   Username: `student01@gec.edu.in`
    -   Password: `CampusDemo123`
-   A local `radtest` using the configured localhost shared secret
    `testing123` returned:
    -   Correct password → `Access-Accept`
    -   Incorrect password → `Access-Reject`
-   This proves basic RADIUS PAP authentication only. It does **not**
    prove WPA2/WPA3-Enterprise or 802.1X Wi-Fi connectivity.
-   Laptop Wi-Fi interface: `wlp8s0`.
-   `iw list` advertises `managed`, `AP`, `AP/VLAN`, and monitor modes.
-   The reported interface combination allows managed + AP concurrently
    on one channel. Actual AP behavior must be tested rather than
    assumed.
-   User has considered USB tethering a phone to the laptop for upstream
    internet while reserving laptop Wi-Fi for the demo AP. This has not
    yet been verified.

### Important current state

FreeRADIUS authentication works locally. The event pipeline, FastAPI
backend, SQLite database, Next.js dashboard, and actual AP/802.1X
integration have **not** yet been implemented or verified.

Do not claim that these unfinished components already work.

------------------------------------------------------------------------

## 2. Required technology stack

Use the following stack unless the existing repository has a compelling,
documented reason to differ:

### Backend

-   Python 3.12+ (use the installed Python version if compatible).
-   FastAPI.
-   Uvicorn.
-   SQLite for the local MVP.
-   SQLAlchemy 2.x or SQLModel for persistence; choose one and use it
    consistently.
-   Pydantic models for API contracts.
-   Pytest for tests.

### Frontend

-   Next.js using the App Router.
-   TypeScript.
-   Tailwind CSS.
-   Use a restrained, professional admin-dashboard design.
-   Use a charting library only if it adds value; keep the dashboard
    lightweight.

### Infrastructure

-   Existing host-installed FreeRADIUS 3.2.8.
-   Do not assume FreeRADIUS is running inside Docker.
-   Do not replace the working host FreeRADIUS installation with a
    container.
-   Do not require Docker for the core local demo.
-   SQLite database stored locally in the project.
-   Environment configuration through `.env` files; provide
    `.env.example` files.

### Suggested repository layout

Adapt to the repository if files already exist. Do not overwrite useful
existing work.

``` text
CampusNet/
├── AGENT.md
├── README.md
├── .gitignore
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PRODUCTION-ROADMAP.md
│   └── DEMO-GUIDE.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/
│   │   ├── services/
│   │   └── workers/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── public/
│   ├── package.json
│   └── .env.example
└── scripts/
    ├── check-radius.sh
    ├── test-radius.sh
    └── setup-demo-user.sh
```

The layout is a recommendation, not a reason to restructure an already
functional repository unnecessarily.

------------------------------------------------------------------------

## 3. Non-negotiable engineering and security rules

1.  **Never use real student passwords or real Google Workspace
    credentials.**
2.  Do not build a Google login page that asks students to enter their
    institutional Google password into CampusNet.
3.  Never store, return, print, or log `User-Password`, cleartext
    passwords, RADIUS shared secrets, private keys, or certificate
    passphrases.
4.  Never put secrets in frontend code, Git, screenshots, API responses,
    or dashboard event records.
5.  Do not expose FreeRADIUS debug output as a public API or dashboard
    data source.
6.  Do not parse the interactive `radiusd -X` console as the production
    event pipeline.
7.  Do not use `chmod 777`, disable SELinux, or weaken system security
    to make the demo work.
8.  Do not overwrite `/etc/raddb` configuration without first inspecting
    it and making a backup.
9.  Do not restart, stop, or reconfigure system services without
    explaining the action and asking the user before any potentially
    disruptive change.
10. Do not invent authentication events, service states, uptime, client
    counts, or network metrics. Clearly label simulated/demo data if any
    is used for visual design.
11. Keep the backend bound to localhost by default. Do not expose an
    unauthenticated admin dashboard or API to the public internet.
12. Validate and sanitize all data read from RADIUS logs.
13. Do not include secrets in exception messages or structured logs.
14. Add rate limiting or sensible polling intervals where appropriate;
    do not poll every few milliseconds.
15. Use parameterized database operations / ORM methods. Never build SQL
    from untrusted strings.
16. Use environment variables for configuration and document safe
    defaults.
17. Avoid unnecessary complexity. This is a time-boxed prototype.

------------------------------------------------------------------------

## 4. Product scope and deliverables

Build the following in priority order. The first three phases are the
core deliverable.

### Phase A --- Real FreeRADIUS event integration

The backend must receive actual authentication outcomes from FreeRADIUS.

Preferred implementation:

1.  Inspect the installed FreeRADIUS configuration and available modules
    before changing anything.
2.  Use a dedicated FreeRADIUS `linelog` instance or another supported,
    structured logging mechanism to write authentication outcomes to a
    dedicated CampusNet event log.
3.  Hook the logger into the correct `post-auth` processing path so that
    successful and rejected authentication attempts are recorded.
4.  Log only safe fields, such as:
    -   timestamp
    -   normalized username
    -   authentication result (`accept` or `reject`)
    -   NAS IP address, if present
    -   NAS port, if present
    -   calling station ID / client MAC, if present
    -   called station ID / AP identifier, if present
    -   authentication method, if safely available
5.  Never log password attributes or shared secrets.
6.  Ensure both `Access-Accept` and `Access-Reject` events are recorded.
7.  Ensure duplicate processing does not create duplicate dashboard
    events.
8.  Ensure the logger does not cause authentication to fail if the event
    log is temporarily unavailable, unless the local FreeRADIUS design
    explicitly requires otherwise.
9.  Handle log rotation and file permissions safely.
10. Document every system-level configuration change and provide a
    rollback procedure.

**Important:** FreeRADIUS configuration syntax varies by version and
package. Inspect the local configuration and module documentation. Do
not blindly paste a generic configuration snippet. Preserve existing
`post-auth` logic and insert the logger without replacing other modules
or policies.

If safely configuring `linelog` is too time-consuming, implement a
clearly documented alternative using FreeRADIUS's supported
detail/accounting facilities. Do not silently fall back to parsing
`radiusd -X`.

Create a script or documented commands to verify the event pipeline by
running valid and invalid `radtest` requests and checking that exactly
the corresponding outcomes appear in the event log.

### Phase B --- FastAPI backend and SQLite

Implement a clean, modular backend.

#### Database model: AuthenticationEvent

Suggested fields:

-   `id`: integer primary key.
-   `event_id`: unique event identifier if one is available.
-   `timestamp`: UTC timestamp, stored consistently.
-   `username`: normalized username; do not store password.
-   `result`: `accept` or `reject`.
-   `nas_ip`: nullable string.
-   `nas_port`: nullable integer.
-   `calling_station_id`: nullable string.
-   `called_station_id`: nullable string.
-   `auth_method`: nullable string.
-   `source`: e.g. `freeradius`.
-   `created_at`: UTC timestamp.

Add appropriate indexes for timestamp, username, and result.

#### Required API endpoints

-   `GET /health`
    -   Returns backend health and database connectivity.
    -   Do not report RADIUS as healthy merely because the API is
        healthy.
-   `GET /api/events`
    -   Returns recent authentication events.
    -   Support pagination and optional filters for result, username,
        and date range.
    -   Default to a reasonable number of records.
-   `GET /api/stats`
    -   Returns total attempts, accepted attempts, rejected attempts,
        acceptance rate, and counts over a defined recent time window.
    -   Avoid division-by-zero errors.
-   `GET /api/radius/status`
    -   Reports whether the configured RADIUS service is reachable or
        active.
    -   On Fedora, service name is likely `radiusd`; verify rather than
        assume.
    -   Do not shell out with user-controlled input.
    -   Use safe, bounded subprocess execution or another appropriate
        local health-check mechanism.
    -   Distinguish `unknown`, `active`, and `inactive`; do not report
        healthy based on an unverified assumption.
-   `GET /api/system/overview`
    -   Combines backend status, RADIUS status, event totals, and latest
        event time.
-   `GET /api/users`
    -   Returns distinct usernames seen in events and their aggregate
        activity.
    -   Do not pretend this is a complete student directory.
-   `GET /api/events/{event_id}`
    -   Returns a single event if useful.

Add CORS configuration restricted to the local frontend origin in
development. Do not use wildcard CORS in a production configuration.

#### Event ingestion worker

-   Implement a robust background worker that tails or polls the
    dedicated event log.
-   Handle partial lines, file truncation, log rotation, restart
    recovery, malformed records, and duplicate records.
-   Do not lose events on normal process restart. Persist a safe
    cursor/offset or use a robust replay strategy with unique event IDs.
-   The worker must not block FastAPI's event loop.
-   Provide clear worker startup/shutdown behavior.
-   Make the log path configurable through an environment variable.
-   If the log is unavailable, report ingestion as degraded instead of
    crashing the API.
-   Do not run a privileged process inside FastAPI.
-   Do not run FastAPI as root just to read a protected RADIUS log.
    Configure a dedicated group/permissions safely and document the
    Fedora/SELinux considerations. If a safe permission setup requires
    administrator action, provide exact manual steps for the user.

### Phase C --- Next.js admin dashboard

Create a professional, responsive dashboard suitable for a principal or
IT/network administrator demonstration.

Design direction: - Product name: CampusNet. - Visual style: clean
enterprise network operations console. - Clear typography, good spacing,
restrained colors, accessible contrast. - Avoid excessive gradients,
glassmorphism, glowing effects, and decorative clutter. - Responsive
desktop-first layout that also works on a phone. - Use realistic but
truthful labels. - Show loading, empty, error, and disconnected
states. - Use actual API data, not hardcoded dashboard numbers.

#### Dashboard overview

Include:

1.  Header with CampusNet identity and local demo/environment indicator.
2.  Service status cards:
    -   API status.
    -   RADIUS status.
    -   Event ingestion status.
3.  Authentication summary:
    -   total attempts.
    -   accepted.
    -   rejected.
    -   acceptance rate.
4.  Authentication activity chart over a selectable recent time window,
    if practical.
5.  Recent authentication events table:
    -   time
    -   username
    -   result badge
    -   NAS / AP identifier
    -   client identifier if available
6.  Search/filter controls:
    -   username search
    -   accepted/rejected filter
    -   recent time range
7.  Last event timestamp and last successful data refresh.
8.  Clear error state when the backend is unreachable.

#### Dashboard behavior

-   Poll the backend at a reasonable interval, e.g. every 5--10 seconds,
    with cleanup on unmount.
-   Do not make the UI appear real-time if it is not.
-   Use API response types and typed fetch helpers.
-   Show empty states when no events exist.
-   Ensure all metrics are computed from persisted backend data.
-   Add a manual refresh action.
-   Avoid fake charts or arbitrary metrics.

### Phase D --- Optional Wi-Fi access point demonstration

Attempt this only after Phases A--C are working.

The laptop Wi-Fi adapter advertises AP mode, but this alone does not
prove WPA2-Enterprise capability. Test actual support.

Potential approach: - Use `hostapd` for a WPA2-Enterprise access point,
configured to forward EAP/RADIUS authentication to the local FreeRADIUS
server. - Use a separate upstream internet connection such as USB
tethering if possible. - Keep the laptop's Wi-Fi adapter dedicated to AP
mode if client+AP concurrency creates problems. - Use an isolated test
SSID such as `CampusNet-Demo`. - Use only fictional demo credentials. -
Restrict the demo to the local test environment. - Do not bridge the
demo network into a college or public network. - Do not expose RADIUS
ports to the internet. - Document how to stop the AP and restore the
previous network configuration.

Do not claim a real 802.1X demo unless a separate client device
successfully connects using an enterprise security profile and the
FreeRADIUS server records the corresponding EAP authentication. A
regular WPA2-Personal hotspot, captive portal, or `radtest` is not an
equivalent substitute.

If actual AP integration is not feasible on the available hardware or
within the time budget, deliver a working RADIUS/API/dashboard demo and
document AP integration as the next phase.

------------------------------------------------------------------------

## 5. Google Workspace and production identity integration

This is a major production consideration.

-   Google Workspace does not automatically provide a generic RADIUS
    authentication endpoint.
-   Do not assume that a Google account password can be checked directly
    by FreeRADIUS.
-   Do not collect Google passwords in a CampusNet form.
-   Do not scrape, reverse-engineer, or imitate Google's login flow.
-   Investigate institution-approved identity federation and supported
    directory/RADIUS integration options.
-   Depending on the institution's Google Workspace edition and
    configuration, Secure LDAP or an identity-provider integration may
    be relevant; verify actual availability and licensing before
    recommending it.
-   Evaluate certificate-based EAP-TLS as a stronger long-term approach,
    with institution-managed device certificates and a trusted CA.
-   If PEAP/MSCHAPv2 is considered, document its identity-provider
    compatibility and security trade-offs rather than assuming it works
    with Google Workspace.
-   Production integration requires approval from the institution's
    IT/network administrators.

For the prototype, use the local FreeRADIUS demo user database only.

------------------------------------------------------------------------

## 6. Production architecture documentation

Create `docs/ARCHITECTURE.md` explaining this flow:

``` text
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
Structured event log
        |
        v
FastAPI ingestion worker
        |
        v
SQLite (prototype) / PostgreSQL (future)
        |
        v
Next.js admin dashboard
```

Explain the roles clearly:

-   Supplicant: student's device.
-   Authenticator: access point or network device controlling access.
-   Authentication server: FreeRADIUS.
-   Identity source: local demo users in the prototype;
    institution-approved directory/IdP in production.
-   VLAN and network policy: network infrastructure, not the RADIUS
    server alone.
-   DHCP/DNS/routing/firewall: required for usable network access after
    authentication.
-   Roaming: depends on AP/controller configuration and supported 802.1X
    roaming behavior.
-   Monitoring: event ingestion and operational dashboard.

Document that Cisco switches/APs need appropriate RADIUS configuration,
shared secrets, source-interface/reachability, and network policies.
Never include actual production secrets.

Create `docs/PRODUCTION-ROADMAP.md` covering:

1.  Institutional identity integration.
2.  RADIUS high availability and redundancy.
3.  Certificate lifecycle and EAP-TLS.
4.  Cisco AP/controller integration.
5.  VLAN assignment and role-based policies.
6.  DHCP/DNS/firewall and internet access.
7.  Logging retention, privacy, and audit policy.
8.  Monitoring and alerting.
9.  Backup, recovery, and disaster planning.
10. Load testing and security review.
11. Pilot rollout in the library.
12. IT approval and student communication.

Do not invent the college's network topology, IP ranges, VLAN IDs,
controller model, Google Workspace edition, or security policy. Mark
them as discovery requirements.

------------------------------------------------------------------------

## 7. Demo experience

Create `docs/DEMO-GUIDE.md` with a reliable 3--5 minute demonstration
sequence:

1.  Start or verify FreeRADIUS.
2.  Start the FastAPI backend and event worker.
3.  Start the Next.js dashboard.
4.  Show the RADIUS service status.
5.  Authenticate a fictional student with the correct password.
6.  Show the `Access-Accept` result and corresponding dashboard event.
7.  Attempt the same account with an incorrect password.
8.  Show `Access-Reject` and the corresponding dashboard event.
9.  Show summary counters updating.
10. Explain what is already real and what remains a production
    integration.

Provide exact local commands after verifying actual package scripts and
paths.

Clearly state in the demo: - RADIUS authentication is real and locally
verified. - The dashboard displays locally captured events. - Google
Workspace integration is not yet connected. - Actual Cisco AP / 802.1X
integration is not yet verified unless Phase D has succeeded. -
Production rollout requires institutional IT approval and infrastructure
configuration.

------------------------------------------------------------------------

## 8. Developer experience and scripts

Provide a simple developer workflow.

Expected commands (adjust to actual implementation):

``` bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

Provide: - `.env.example` for backend and frontend. - `.gitignore` that
excludes `.env`, virtual environments, node_modules, SQLite DBs if they
contain personal/demo data, logs, keys, certificates, build output, and
caches. - `README.md` with setup, architecture, environment variables,
API docs, test commands, and troubleshooting. - Tests for database
models, API endpoints, event parser, duplicate handling, and malformed
log records. - A health-check script for the local RADIUS service. - A
test script that runs correct and incorrect `radtest` checks without
printing secrets. - A sample event fixture containing fake usernames and
no secrets.

Use `127.0.0.1` for local development by default. If another device
needs to access the dashboard during a demo, explain the LAN exposure
implications and require an explicit opt-in configuration.

------------------------------------------------------------------------

## 9. Implementation workflow for the coding agent

Work autonomously, but do not make risky system changes silently.

### First: inspect

1.  Inspect the existing repository and identify its current state.
2.  Read existing files before modifying them.
3.  Check whether any frontend/backend scaffolding already exists.
4.  Check the locally installed FreeRADIUS version and relevant
    configuration paths using read-only commands.
5.  Identify whether `linelog` is enabled and inspect the local
    `post-auth` section.
6.  Write a short implementation plan and list any system-level actions
    requiring user approval.

### Then: implement

1.  Build the backend data model, API, parser, and tests.
2.  Implement the FreeRADIUS event integration using the installed
    version's actual configuration.
3.  Do not alter the RADIUS config until a backup exists and the user
    approves the specific change.
4.  Build the frontend and connect it to the real API.
5.  Add documentation and demo scripts.
6.  Run tests, lint, type checks, and build commands.
7.  Verify the complete data flow with successful and failed local
    RADIUS requests.

### Quality gates

Do not declare completion until:

-   [ ] Existing FreeRADIUS installation is preserved.
-   [ ] Valid local RADIUS credentials return `Access-Accept`.
-   [ ] Invalid local RADIUS credentials return `Access-Reject`.
-   [ ] Both outcomes create safe structured event records.
-   [ ] Passwords and shared secrets never enter event records.
-   [ ] Event records are persisted in SQLite.
-   [ ] API endpoints return actual database values.
-   [ ] Dashboard displays actual API data.
-   [ ] Dashboard handles backend disconnection and empty data.
-   [ ] Backend and frontend tests pass.
-   [ ] Frontend production build succeeds.
-   [ ] Setup and demo documentation is complete.
-   [ ] Any incomplete Wi-Fi/802.1X work is clearly disclosed.

------------------------------------------------------------------------

## 10. Prioritization under the one-day deadline

Use this order:

  -----------------------------------------------------------------------
  Priority                Deliverable             Importance
  ----------------------- ----------------------- -----------------------
  P0                      Safe FreeRADIUS event   Critical
                          logging                 

  P0                      FastAPI + SQLite event  Critical
                          ingestion               

  P0                      Next.js dashboard with  Critical
                          real events             

  P0                      Valid/invalid           Critical
                          authentication demo     

  P1                      Stats, filtering,       High
                          responsive UI           

  P1                      Architecture and        High
                          production roadmap      

  P2                      Laptop-hosted           Optional
                          WPA2-Enterprise AP      

  P2                      Google Workspace        Future, requires
                          integration             institution approval

  P2                      Cisco production        Future, requires IT
                          integration             access
  -----------------------------------------------------------------------

If time is limited, finish P0 properly rather than starting multiple
unfinished integrations.

------------------------------------------------------------------------

## 11. Agent communication and coding style

-   Explain the purpose of important architectural decisions briefly.
-   Prefer small, coherent modules over a monolithic implementation.
-   Keep types explicit.
-   Use clear naming and meaningful error handling.
-   Do not add dependencies without a reason.
-   Do not overengineer for hypothetical scale.
-   Do not replace a working component merely to use a preferred
    framework.
-   Do not ask the user questions that can be answered by inspecting the
    repository or local configuration.
-   When a task requires privileged access or a system-level change,
    explain exactly what will change and provide the command for the
    user to execute or approve.
-   After each milestone, report:
    -   files created/changed
    -   commands run
    -   tests passed/failed
    -   what is genuinely working
    -   what remains incomplete
    -   next recommended action

**Final standard:** CampusNet should be a transparent, credible
engineering prototype. Prioritize a real authentication-to-dashboard
data path over visual polish or claims of production readiness.
