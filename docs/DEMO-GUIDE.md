# CampusNet demo

1. Verify FreeRADIUS is running: `systemctl is-active radiusd`.
2. Start the backend and frontend using the commands in `README.md`.
3. Open the dashboard and show API, RADIUS, and ingestion status.
4. Run a valid fictional `radtest` and show `Access-Accept` plus the dashboard event.
5. Run the same fictional account with a wrong password and show `Access-Reject`.
6. Show counters and explain that the captured event path is local and real.

The demo user is fictional. Google Workspace, Cisco AP/802.1X, and production rollout are not connected unless separately verified.

