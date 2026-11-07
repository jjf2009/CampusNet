# FreeRADIUS integration gate

FreeRADIUS 3.2.8 is installed on the host. The repository does not modify `/etc/raddb` automatically.

Before applying integration:

1. Inspect enabled modules and the active `post-auth` section as an administrator.
2. Back up `/etc/raddb` and record the backup path.
3. Add a dedicated `linelog` instance that writes JSON Lines containing only timestamp, normalized username, result, NAS fields, station identifiers, and safe authentication method.
4. Invoke it from the existing `post-auth` flow without replacing existing modules.
5. Configure a dedicated readable event-log path and group permissions; preserve SELinux enforcement.
6. Validate configuration with `radiusd -XC`, then run valid and invalid `radtest` requests.
7. Reload only after approval and retain rollback commands to restore the backup.

Never include `User-Password`, shared secrets, private keys, or debug output. The application accepts JSON Lines through `RADIUS_EVENT_LOG`; a fixture can be used for UI development.

## WPA2-Enterprise laptop AP

The intended local topology is USB tethering into the laptop, then a laptop Wi-Fi AP named `CampusNet-Demo` for a second test phone. The inspected laptop adapter is `wlp8s0` (Realtek RTL8852BE, `rtw89_8852be`) and advertises AP mode plus one managed interface on the same channel. The current host does not have `hostapd` installed.

The repository provides guarded scripts:

- `scripts/start-campusnet-ap.sh` configures the AP interface, DHCP, IPv4 forwarding, NAT, hostapd, and a localhost RADIUS target.
- `scripts/stop-campusnet-ap.sh` stops the processes, removes the demo nftables table, restores forwarding, and asks NetworkManager to restore the original Wi-Fi connection.
- `scripts/start-campusnet-ap-local.sh` / `scripts/stop-campusnet-ap-local.sh` are an **auth-only** variant: they bring up the same WPA2-Enterprise SSID pointed at localhost RADIUS but make **no** forwarding, NAT, or firewall changes and need no upstream interface. The connecting device authenticates (and appears on the dashboard) with no internet. This is the recommended demo path when internet on the client is not required; see `docs/DEMO-GUIDE.md` §8.4.
- `scripts/campusnet-ap.conf.example` documents non-secret settings. The real shared secret must be supplied through `/etc/campusnet-ap.env` with mode `600` or an environment variable.
- `scripts/configure-radius-campusnet.sh` creates a protected backup, enables PEAP when the installed EAP configuration has the expected default, installs one safe `linelog` instance that records the reply packet type, inserts the post-auth hook, grants the backend user read access to the event directory, and validates with `radiusd -XC` without restarting the service.

Before running the start script, install `hostapd`, connect USB tethering, verify the upstream interface with `nmcli device status`, and confirm the FreeRADIUS localhost client accepts RADIUS requests from hostapd. The script requires `CONFIRM_CAMPUSNET_AP=YES` and root privileges because it changes the Wi-Fi interface, forwarding, and firewall state. It must not be run while relying on the laptop Wi-Fi connection for internet; USB tethering must provide the upstream route.

To prepare the RADIUS side from the repository root:

```bash
sudo env CONFIRM_CAMPUSNET_RADIUS=YES \
  APP_USER="$USER" \
  scripts/configure-radius-campusnet.sh
```

Review the printed backup path and validation result. Only after validation succeeds should you restart FreeRADIUS:

```bash
sudo systemctl restart radiusd
systemctl is-active radiusd
```

The script intentionally does not print or modify RADIUS shared secrets. If validation fails, restore the printed backup and do not restart the service.
