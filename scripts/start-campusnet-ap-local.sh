#!/usr/bin/env bash
# CampusNet demo access point — AUTH-ONLY (no internet / NAT / forwarding).
#
# Turns the laptop Wi-Fi into a WPA2-Enterprise SSID that forwards 802.1X/EAP
# to the local FreeRADIUS server. A connecting device authenticates (and the
# outcome appears on the CampusNet dashboard) but gets no internet — that is by
# design and sufficient for the demo. 802.1X auth completes during association,
# before DHCP/internet would matter.
#
# Unlike start-campusnet-ap.sh, this makes NO forwarding, NAT, or firewall
# changes and needs no upstream interface. Fully reversible via
# stop-campusnet-ap-local.sh.
#
# Usage:
#   sudo env CONFIRM_CAMPUSNET_AP=YES bash scripts/start-campusnet-ap-local.sh

set -Eeuo pipefail

STATE_DIR="${CAMPUSNET_AP_STATE_DIR:-/run/campusnet-ap}"
ENV_FILE="${CAMPUSNET_AP_ENV:-/etc/campusnet-ap.env}"
WIFI_IFACE="${WIFI_IFACE:-wlp8s0}"
AP_SSID="${AP_SSID:-CampusNet-Demo}"
AP_CHANNEL="${AP_CHANNEL:-11}"
AP_ADDRESS="${AP_ADDRESS:-10.42.0.1/24}"
DHCP_RANGE_START="${DHCP_RANGE_START:-10.42.0.20}"
DHCP_RANGE_END="${DHCP_RANGE_END:-10.42.0.120}"
RADIUS_ADDR="${RADIUS_ADDR:-127.0.0.1}"
RADIUS_AUTH_PORT="${RADIUS_AUTH_PORT:-1812}"
RADIUS_ACCT_PORT="${RADIUS_ACCT_PORT:-1813}"
RADIUS_SHARED_SECRET="${RADIUS_SHARED_SECRET:-}"
RADIUS_SERVICE_NAME="${RADIUS_SERVICE_NAME:-radiusd}"

die() { echo "ERROR: $*" >&2; exit 1; }
require_cmd() { command -v "$1" >/dev/null 2>&1 || die "Required command missing: $1"; }

[[ "${EUID}" -eq 0 ]] || die "Run as root; this changes the Wi-Fi interface state."
[[ "${CONFIRM_CAMPUSNET_AP:-}" == "YES" ]] || die "Set CONFIRM_CAMPUSNET_AP=YES after reviewing the demo change."

if [[ -r "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

require_cmd nmcli
require_cmd ip
require_cmd hostapd
require_cmd dnsmasq
require_cmd systemctl
systemctl is-active --quiet "$RADIUS_SERVICE_NAME" || die "RADIUS service is not active: $RADIUS_SERVICE_NAME"
[[ -n "$RADIUS_SHARED_SECRET" && "$RADIUS_SHARED_SECRET" != replace-locally ]] \
  || die "Set RADIUS_SHARED_SECRET outside the repository (e.g. $ENV_FILE, mode 600)."
ip link show "$WIFI_IFACE" >/dev/null 2>&1 || die "Wi-Fi interface not found: $WIFI_IFACE"

mkdir -p "$STATE_DIR"
chmod 700 "$STATE_DIR"
[[ ! -f "$STATE_DIR/state" ]] || die "CampusNet AP appears active; run stop-campusnet-ap-local.sh first."

ORIGINAL_CONNECTION="$(nmcli -t -f GENERAL.CONNECTION device show "$WIFI_IFACE" | sed 's/^GENERAL.CONNECTION://')"
printf 'WIFI_IFACE=%q\nORIGINAL_CONNECTION=%q\nMODE=%q\n' \
  "$WIFI_IFACE" "$ORIGINAL_CONNECTION" "local-auth-only" > "$STATE_DIR/state"
chmod 600 "$STATE_DIR/state"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cleanup_on_error() { echo "Startup failed; attempting rollback." >&2; "$SCRIPT_DIR/stop-campusnet-ap-local.sh" || true; }
trap cleanup_on_error ERR

# Hand the interface to us and give it the AP gateway address.
nmcli device disconnect "$WIFI_IFACE" >/dev/null 2>&1 || true
nmcli device set "$WIFI_IFACE" managed no
ip link set "$WIFI_IFACE" down
ip addr flush dev "$WIFI_IFACE"
ip addr add "$AP_ADDRESS" dev "$WIFI_IFACE"
ip link set "$WIFI_IFACE" up

# DHCP only — no upstream DNS, no NAT. Connecting devices get an address so the
# association completes cleanly; they will correctly show "no internet".
cat > "$STATE_DIR/dnsmasq.conf" <<EOF
interface=$WIFI_IFACE
bind-interfaces
listen-address=${AP_ADDRESS%/*}
dhcp-range=$DHCP_RANGE_START,$DHCP_RANGE_END,255.255.255.0,12h
dhcp-option=3,${AP_ADDRESS%/*}
no-resolv
port=0
log-facility=$STATE_DIR/dnsmasq.log
pid-file=$STATE_DIR/dnsmasq.pid
EOF

cat > "$STATE_DIR/hostapd.conf" <<EOF
interface=$WIFI_IFACE
driver=nl80211
ssid=$AP_SSID
country_code=IN
hw_mode=g
channel=$AP_CHANNEL
ieee80211n=1
wmm_enabled=1
auth_algs=1
ieee8021x=1
wpa=2
wpa_key_mgmt=WPA-EAP
rsn_pairwise=CCMP
auth_server_addr=$RADIUS_ADDR
auth_server_port=$RADIUS_AUTH_PORT
auth_server_shared_secret=$RADIUS_SHARED_SECRET
acct_server_addr=$RADIUS_ADDR
acct_server_port=$RADIUS_ACCT_PORT
acct_server_shared_secret=$RADIUS_SHARED_SECRET
own_ip_addr=127.0.0.1
ctrl_interface=$STATE_DIR/hostapd
logger_syslog=-1
logger_syslog_level=2
EOF
chmod 600 "$STATE_DIR/hostapd.conf"

dnsmasq --conf-file="$STATE_DIR/dnsmasq.conf"
hostapd -B -P "$STATE_DIR/hostapd.pid" -f "$STATE_DIR/hostapd.log" "$STATE_DIR/hostapd.conf"
trap - ERR

echo "CampusNet AP (auth-only) started: SSID=$AP_SSID interface=$WIFI_IFACE"
echo "hostapd log: $STATE_DIR/hostapd.log  (look for AP-ENABLED)"
echo
echo "On the test phone, join '$AP_SSID':"
echo "  Security: WPA/WPA2-Enterprise | EAP: PEAP | Phase-2: MSCHAPV2"
echo "  Identity: student01@gec.edu.in | Password: (the demo password)"
echo "  CA certificate: Do not validate (server cert is self-signed)"
echo
echo "The phone will authenticate and show on the dashboard; 'no internet' is expected."
echo "Stop + restore Wi-Fi with: sudo bash scripts/stop-campusnet-ap-local.sh"
