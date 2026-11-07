#!/usr/bin/env bash
# Stop the auth-only CampusNet demo AP and restore normal Wi-Fi.
# Pairs with start-campusnet-ap-local.sh. Makes no firewall/NAT changes
# because the auth-only start script never made any.
#
# Usage: sudo bash scripts/stop-campusnet-ap-local.sh

set -Eeuo pipefail

STATE_DIR="${CAMPUSNET_AP_STATE_DIR:-/run/campusnet-ap}"
WIFI_IFACE="${WIFI_IFACE:-wlp8s0}"

[[ "${EUID}" -eq 0 ]] || { echo "ERROR: run as root" >&2; exit 1; }
[[ -d "$STATE_DIR" ]] || { echo "CampusNet AP state not found: nothing to stop"; exit 0; }

if [[ -f "$STATE_DIR/hostapd.pid" ]]; then kill "$(cat "$STATE_DIR/hostapd.pid")" 2>/dev/null || true; fi
if [[ -f "$STATE_DIR/dnsmasq.pid" ]]; then kill "$(cat "$STATE_DIR/dnsmasq.pid")" 2>/dev/null || true; fi

ORIGINAL_CONNECTION=""
HAVE_FIREWALLD="no"
ORIGINAL_AP_ZONE=""
if [[ -f "$STATE_DIR/state" ]]; then
  # shellcheck disable=SC1091
  source "$STATE_DIR/state"
fi

# Restore the AP interface's firewall zone (undo the demo trusted-zone move).
if [[ "$HAVE_FIREWALLD" == "yes" ]] && command -v firewall-cmd >/dev/null 2>&1; then
  firewall-cmd --zone=trusted --remove-interface="$WIFI_IFACE" >/dev/null 2>&1 || true
  if [[ -n "$ORIGINAL_AP_ZONE" && "$ORIGINAL_AP_ZONE" != "no zone" ]]; then
    firewall-cmd --zone="$ORIGINAL_AP_ZONE" --add-interface="$WIFI_IFACE" >/dev/null 2>&1 || true
  fi
fi

ip addr flush dev "$WIFI_IFACE" 2>/dev/null || true
nmcli device set "$WIFI_IFACE" managed yes || true
# Let NetworkManager pick the right profile for the device; fall back to the
# captured connection name only if that fails.
nmcli device connect "$WIFI_IFACE" >/dev/null 2>&1 \
  || { [[ -n "$ORIGINAL_CONNECTION" && "$ORIGINAL_CONNECTION" != "--" ]] \
       && nmcli connection up "$ORIGINAL_CONNECTION" >/dev/null 2>&1; } \
  || true

rm -rf "$STATE_DIR"
echo "CampusNet AP (auth-only) stopped; Wi-Fi handed back to NetworkManager."
