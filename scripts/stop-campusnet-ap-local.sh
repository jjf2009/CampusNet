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
if [[ -f "$STATE_DIR/state" ]]; then
  # shellcheck disable=SC1091
  source "$STATE_DIR/state"
fi

ip addr flush dev "$WIFI_IFACE" 2>/dev/null || true
nmcli device set "$WIFI_IFACE" managed yes || true
if [[ -n "${ORIGINAL_CONNECTION:-}" && "$ORIGINAL_CONNECTION" != "--" ]]; then
  nmcli connection up "$ORIGINAL_CONNECTION" || true
fi

rm -rf "$STATE_DIR"
echo "CampusNet AP (auth-only) stopped; NetworkManager restoration attempted."
