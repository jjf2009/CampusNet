#!/usr/bin/env bash
set -Eeuo pipefail

STATE_DIR="${CAMPUSNET_AP_STATE_DIR:-/run/campusnet-ap}"
[[ "${EUID}" -eq 0 ]] || { echo "ERROR: run as root" >&2; exit 1; }
[[ -d "$STATE_DIR" ]] || { echo "CampusNet AP state not found: nothing to stop"; exit 0; }

if [[ -f "$STATE_DIR/hostapd.pid" ]]; then kill "$(cat "$STATE_DIR/hostapd.pid")" 2>/dev/null || true; fi
if [[ -f "$STATE_DIR/dnsmasq.pid" ]]; then kill "$(cat "$STATE_DIR/dnsmasq.pid")" 2>/dev/null || true; fi
nft delete table ip campusnet_demo 2>/dev/null || true

if [[ -f "$STATE_DIR/state" ]]; then
  # shellcheck disable=SC1091
  source "$STATE_DIR/state"
  sysctl -w "net.ipv4.ip_forward=${ORIGINAL_FORWARDING:-0}" >/dev/null || true
  firewall-cmd --zone=trusted --remove-interface="$WIFI_IFACE" >/dev/null 2>&1 || true
  if [[ "${ORIGINAL_TRUSTED_FORWARD:-no}" != "yes" ]]; then
    firewall-cmd --zone=trusted --remove-forward >/dev/null 2>&1 || true
  fi
  if [[ "${ORIGINAL_UPSTREAM_MASQUERADE:-no}" != "yes" ]]; then
    firewall-cmd --zone="${UPSTREAM_ZONE:-FedoraWorkstation}" --remove-masquerade >/dev/null 2>&1 || true
  fi
  if [[ -n "${ORIGINAL_AP_ZONE:-}" && "${ORIGINAL_AP_ZONE}" != "no zone" ]]; then
    firewall-cmd --zone="$ORIGINAL_AP_ZONE" --add-interface="$WIFI_IFACE" >/dev/null 2>&1 || true
  fi
  ip addr flush dev "$WIFI_IFACE" 2>/dev/null || true
  nmcli device set "$WIFI_IFACE" managed yes || true
  if [[ -n "${ORIGINAL_CONNECTION:-}" && "$ORIGINAL_CONNECTION" != "--" ]]; then
    nmcli connection up "$ORIGINAL_CONNECTION" || true
  fi
fi
rm -rf "$STATE_DIR"
echo "CampusNet AP stopped; NetworkManager restoration attempted."
