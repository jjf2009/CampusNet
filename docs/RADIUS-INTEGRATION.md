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

