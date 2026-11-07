#!/usr/bin/env bash
# Fix: the CampusNet accept hook (campusnet_event) was placed at virtual-server
# scope instead of inside post-auth {}, so FreeRADIUS never ran it and
# Access-Accept events were not logged (only rejects).
#
# This script:
#   1. backs up the real site config (follows the sites-enabled symlink),
#   2. removes any floating bare `campusnet_event` reference,
#   3. inserts `campusnet_event` as the first statement inside post-auth {},
#   4. validates with `radiusd -XC`, auto-restoring the backup on failure.
#
# It does NOT restart radiusd — review the output, then restart yourself.
# Idempotent: safe to run more than once.
#
# Usage:  sudo bash scripts/fix-campusnet-accept-hook.sh
#         sudo bash scripts/fix-campusnet-accept-hook.sh /etc/raddb/sites-enabled/default

set -Eeuo pipefail

SITE_LINK="${1:-/etc/raddb/sites-enabled/default}"
[[ $EUID -eq 0 ]] || { echo "ERROR: run with sudo." >&2; exit 1; }
[[ -e "$SITE_LINK" ]] || { echo "ERROR: not found: $SITE_LINK" >&2; exit 1; }

SITE="$(readlink -f "$SITE_LINK")"
SITE_DIR="$(dirname "$SITE")"
STAMP="$(date +%Y%m%d-%H%M%S)"

# CRITICAL: the backup must NOT live inside sites-enabled/ (or wherever the
# site file lives, if that dir is scanned). FreeRADIUS loads every file in
# sites-enabled/, so a backup copy there defines a second `server default {}`
# and breaks the config with a "Duplicate virtual server" error.
BAK_DIR="/var/backups/campusnet-radius"
mkdir -p "$BAK_DIR"; chmod 700 "$BAK_DIR"
BAK="$BAK_DIR/$(basename "$SITE").$STAMP.bak"

# Clean up any stray backups a previous version of this script may have left
# next to the site file — those cause the duplicate-server error.
shopt -s nullglob
for leak in "$SITE_DIR"/*.campusnet.bak.*; do
  echo "Removing stray backup from the sites directory: $leak"
  rm -f "$leak"
done
shopt -u nullglob

grep -Eq '^[[:space:]]*post-auth[[:space:]]*\{[[:space:]]*$' "$SITE" \
  || { echo "ERROR: could not find a 'post-auth {' line in $SITE" >&2; exit 1; }
grep -q 'campusnet_event' "$SITE" \
  || echo "NOTE: no existing campusnet_event reference found; inserting fresh."

cp -a "$SITE" "$BAK"
echo "Backup (outside sites dir): $BAK"

# 1) Drop any bare 'campusnet_event' hook wherever it floats.
#    'campusnet_event_reject' has a suffix, so it is left untouched.
sed -i '/^[[:space:]]*campusnet_event[[:space:]]*$/d' "$SITE"

# 2) Insert the hook as the first statement inside post-auth {}.
sed -i '0,/^[[:space:]]*post-auth[[:space:]]*{[[:space:]]*$/s//&\n\tcampusnet_event/' "$SITE"

echo "--- campusnet hooks now (line : text) ---"
grep -n 'campusnet_event' "$SITE"

echo "--- validating (radiusd -XC) ---"
XC="/tmp/campusnet-xc-$STAMP.log"
if radiusd -XC >"$XC" 2>&1; then
  tail -3 "$XC"
  echo
  echo "OK. Review placement above, then:"
  echo "  sudo systemctl restart radiusd && systemctl is-active radiusd"
  echo "Rollback if needed:"
  echo "  sudo cp -a '$BAK' '$SITE' && sudo systemctl restart radiusd"
else
  echo "VALIDATION FAILED — restoring backup, no change kept." >&2
  cp -a "$BAK" "$SITE"
  grep -E '(^/etc/raddb/|Error|ERROR|Failed|Invalid|Unknown|parse|syntax)' "$XC" | tail -20 >&2 || tail -20 "$XC" >&2
  exit 1
fi
