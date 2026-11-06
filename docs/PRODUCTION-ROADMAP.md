# Production roadmap

This prototype delivers a real, local RADIUS → event → dashboard path. The
following are required to move toward a supervised campus deployment. All
topology, IP ranges, VLAN IDs, controller models, Google Workspace licensing,
and security policies are **discovery requirements** — none are assumed here.

## 1. Institutional identity integration
Select an institution-approved option. Google Workspace does not expose a
generic RADIUS endpoint; evaluate Secure LDAP (edition/licensing dependent)
or an IdP federation. Prefer EAP-TLS device certificates long term. Do not
collect Google passwords. Requires IT approval.

## 2. RADIUS high availability and redundancy
Run redundant FreeRADIUS instances behind the authenticators' primary/
secondary server lists. Define failover, shared policy/config management,
and health checks.

## 3. Certificate lifecycle and EAP-TLS
Establish a trusted CA, device/server certificate issuance and rotation,
revocation (CRL/OCSP), and supplicant trust provisioning via MDM.

## 4. Cisco AP / controller integration
Configure approved RADIUS clients (NAS), shared secrets (never in Git),
source-interface/reachability, CoA, and 802.1X on the WLAN/switchports.

## 5. VLAN assignment and role-based policies
Map authentication outcomes to VLANs/roles via RADIUS attributes; define
role policy at the controller and downstream enforcement.

## 6. DHCP / DNS / firewall and internet access
Provision per-VLAN DHCP/DNS, routing, and firewall policy so an accepted
session yields usable, policy-bounded connectivity.

## 7. Logging retention, privacy, and audit policy
Define retention windows, PII minimization (already: no secrets logged),
access controls on event data, and an audit trail. Comply with institutional
privacy policy.

## 8. Monitoring and alerting
Add service/uptime monitoring for RADIUS and the pipeline, ingestion-lag and
reject-spike alerts, and dashboards for operations staff.

## 9. Backup, recovery, and disaster planning
Back up config, certificates (securely), and the event store (PostgreSQL in
production). Document restore and failover runbooks; test them.

## 10. Load testing and security review
Load-test RADIUS and the API at expected peak. Conduct a security review:
authN/authZ on the dashboard, network exposure, dependency and secret
handling.

## 11. Pilot rollout in the library
Run a controlled pilot on an isolated SSID/VLAN with a small user group.
Measure success/reject rates, roaming, and support load before expanding.

## 12. IT approval and student communication
Obtain formal IT/network administrator approval. Communicate the rollout,
privacy posture, supported devices, and support channels to students.

---

Prototype gaps disclosed: dashboard is unauthenticated (localhost only);
store is SQLite; identity is a single local demo user; AP/802.1X (Phase D)
and Google Workspace/Cisco integration are **not** verified or claimed.
