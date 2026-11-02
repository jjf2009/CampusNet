#!/usr/bin/env bash
set -Eeuo pipefail

RADIUS_DIR="${RADIUS_DIR:-/etc/raddb}"
EVENT_DIR="${CAMPUSNET_EVENT_DIR:-/var/log/campusnet}"
EVENT_LOG="$EVENT_DIR/radius-events.jsonl"
RADIUS_USER="${RADIUS_USER:-radiusd}"
APP_USER="${APP_USER:-${SUDO_USER:-}}"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${CAMPUSNET_RADIUS_BACKUP_DIR:-/var/backups}"
BACKUP_FILE="$BACKUP_DIR/campusnet-radius-$STAMP.tar.gz"

die() { echo "ERROR: $*" >&2; exit 1; }
[[ "${EUID}" -eq 0 ]] || die "Run as root."
[[ "${CONFIRM_CAMPUSNET_RADIUS:-}" == "YES" ]] || die "Set CONFIRM_CAMPUSNET_RADIUS=YES after reviewing this change."
command -v radiusd >/dev/null || die "radiusd is not installed."
command -v setfacl >/dev/null || die "setfacl is required for safe backend log access."
[[ -d "$RADIUS_DIR" ]] || die "RADIUS directory not found: $RADIUS_DIR"
[[ -e "$RADIUS_DIR/mods-enabled/eap" ]] || die "EAP module is not enabled: $RADIUS_DIR/mods-enabled/eap"
[[ -e "$RADIUS_DIR/sites-enabled/default" ]] || die "default virtual server not found."

EAP_FILE="$RADIUS_DIR/mods-enabled/eap"
SITE_FILE="$RADIUS_DIR/sites-enabled/default"
LINETO="$RADIUS_DIR/mods-enabled/campusnet_event"

if [[ -e "$LINETO" ]] || grep -q 'campusnet_event' "$SITE_FILE"; then
  die "CampusNet RADIUS integration already appears to exist; inspect manually instead of overwriting it."
fi

mkdir -p "$BACKUP_DIR"
umask 077
tar -czf "$BACKUP_FILE" -C / etc/raddb
echo "Created protected backup: $BACKUP_FILE"

install -d -o root -g "$RADIUS_USER" -m 0750 "$EVENT_DIR"
setfacl -m "g:$RADIUS_USER:rwx" "$EVENT_DIR"
if [[ -n "$APP_USER" ]]; then
  setfacl -m "u:$APP_USER:rx" "$EVENT_DIR"
  setfacl -d -m "u:$APP_USER:rX,g:$RADIUS_USER:rX" "$EVENT_DIR"
fi

cat > "$LINETO" <<EOF
linelog campusnet_event {
    filename = $EVENT_LOG
    permissions = 0640
    group = $RADIUS_USER
    format = "{\"timestamp\":\"%T\",\"username\":\"%{User-Name}\",\"result\":\"%{reply:Packet-Type}\",\"nas_ip\":\"%{NAS-IP-Address}\",\"nas_port\":\"%{NAS-Port}\",\"calling_station_id\":\"%{Calling-Station-Id}\",\"called_station_id\":\"%{Called-Station-Id}\",\"auth_method\":\"%{control:Auth-Type}\",\"source\":\"freeradius\"}"
}
EOF
chown root:"$RADIUS_USER" "$LINETO"
chmod 0640 "$LINETO"

if grep -Eq '^[[:space:]]*default_eap_type[[:space:]]*=[[:space:]]*md5[[:space:]]*$' "$EAP_FILE"; then
  sed -i '0,/^[[:space:]]*default_eap_type[[:space:]]*=[[:space:]]*md5[[:space:]]*$/s//    default_eap_type = peap/' "$EAP_FILE"
elif ! grep -Eq '^[[:space:]]*default_eap_type[[:space:]]*=[[:space:]]*peap[[:space:]]*$' "$EAP_FILE"; then
  die "EAP default type is not the expected md5/peap form; inspect $EAP_FILE manually. Backup remains at $BACKUP_FILE"
fi

TMP_SITE="$(mktemp)"
awk '
  BEGIN { in_post=0; depth=0; inserted=0 }
  !in_post && $0 ~ /^[[:space:]]*post-auth[[:space:]]*\{/ { in_post=1; depth=1; print; next }
  in_post {
    opens=gsub(/\{/, "{"); closes=gsub(/\}/, "}")
    if (depth == 1 && closes > opens && !inserted) {
      print "    campusnet_event"
      inserted=1
    }
    depth += opens - closes
    print
    if (depth == 0) in_post=0
    next
  }
  { print }
  END { if (!inserted) exit 2 }
' "$SITE_FILE" > "$TMP_SITE" || { rm -f "$TMP_SITE"; die "Could not locate a safe post-auth insertion point. Backup remains at $BACKUP_FILE"; }
install -o root -g root -m 0640 "$TMP_SITE" "$SITE_FILE"
rm -f "$TMP_SITE"

echo "Validating FreeRADIUS configuration..."
if ! radiusd -XC >/tmp/campusnet-radius-check-"$STAMP".log 2>&1; then
  echo "Validation failed. Restore with: tar -xzf '$BACKUP_FILE' -C /" >&2
  echo "Validation output is in /tmp/campusnet-radius-check-$STAMP.log" >&2
  echo "First relevant validation lines (secrets redacted):" >&2
  sed -E 's/(secret|password|User-Password)[^[:space:]]*/\1=<REDACTED>/Ig' \
    /tmp/campusnet-radius-check-"$STAMP".log \
    | grep -E '(^/etc/raddb/|Error|ERROR|Failed|Invalid|Unknown|parse|syntax)' \
    | tail -30 >&2 || true
  exit 1
fi
rm -f /tmp/campusnet-radius-check-"$STAMP".log
echo "Configuration validated. No service was restarted."
echo "Review the change, then run: sudo systemctl restart radiusd"
echo "Event log: $EVENT_LOG"
