#!/usr/bin/env bash
set -Eeuo pipefail

STATE_DIR="${CAMPUSNET_AP_STATE_DIR:-/run/campusnet-ap}"
ENV_FILE="${CAMPUSNET_AP_ENV:-/etc/campusnet-ap.env}"
WIFI_IFACE="${WIFI_IFACE:-wlp8s0}"
UPSTREAM_IFACE="${UPSTREAM_IFACE:-}"
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

[[ "${EUID}" -eq 0 ]] || die "Run as root; this changes Wi-Fi, forwarding, and firewall state."
[[ "${CONFIRM_CAMPUSNET_AP:-}" == "YES" ]] || die "Set CONFIRM_CAMPUSNET_AP=YES after reviewing the demo change."

if [[ -r "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

require_cmd nmcli
require_cmd ip
require_cmd nft
require_cmd sysctl
require_cmd firewall-cmd
require_cmd hostapd
require_cmd dnsmasq
systemctl is-active --quiet "$RADIUS_SERVICE_NAME" || die "RADIUS service is not active: $RADIUS_SERVICE_NAME"
[[ -n "$RADIUS_SHARED_SECRET" && "$RADIUS_SHARED_SECRET" != replace-locally ]] || die "Set RADIUS_SHARED_SECRET outside the repository."
[[ -n "$UPSTREAM_IFACE" ]] || UPSTREAM_IFACE="$(ip route get 1.1.1.1 | awk '/dev/ {for (i=1;i<=NF;i++) if ($i=="dev") {print $(i+1); exit}}')"
[[ -n "$UPSTREAM_IFACE" ]] || die "No upstream interface found; connect USB tethering first."
[[ "$UPSTREAM_IFACE" != "$WIFI_IFACE" ]] || die "USB upstream must not be the Wi-Fi AP interface."
ip link show "$WIFI_IFACE" >/dev/null 2>&1 || die "Wi-Fi interface not found: $WIFI_IFACE"
ip link show "$UPSTREAM_IFACE" >/dev/null 2>&1 || die "Upstream interface not found: $UPSTREAM_IFACE"
ip route get 1.1.1.1 >/dev/null 2>&1 || die "No default route; confirm USB tethering provides internet."

mkdir -p "$STATE_DIR"
chmod 700 "$STATE_DIR"
[[ ! -f "$STATE_DIR/state" ]] || die "CampusNet AP appears active; run stop-campusnet-ap.sh first."
ORIGINAL_CONNECTION="$(nmcli -t -f GENERAL.CONNECTION device show "$WIFI_IFACE" | sed 's/^GENERAL.CONNECTION://')"
ORIGINAL_FORWARDING="$(sysctl -n net.ipv4.ip_forward)"
ORIGINAL_AP_ZONE="$(firewall-cmd --get-zone-of-interface="$WIFI_IFACE" 2>/dev/null || true)"
UPSTREAM_ZONE="$(firewall-cmd --get-zone-of-interface="$UPSTREAM_IFACE" 2>/dev/null || true)"
[[ -n "$UPSTREAM_ZONE" && "$UPSTREAM_ZONE" != "no zone" ]] || UPSTREAM_ZONE="$(firewall-cmd --get-default-zone)"
ORIGINAL_UPSTREAM_MASQUERADE="$(firewall-cmd --zone="$UPSTREAM_ZONE" --query-masquerade 2>/dev/null || echo no)"
ORIGINAL_TRUSTED_FORWARD="$(firewall-cmd --zone=trusted --query-forward 2>/dev/null || echo no)"
printf 'WIFI_IFACE=%q\nUPSTREAM_IFACE=%q\nORIGINAL_CONNECTION=%q\nORIGINAL_FORWARDING=%q\nORIGINAL_AP_ZONE=%q\nUPSTREAM_ZONE=%q\nORIGINAL_UPSTREAM_MASQUERADE=%q\nORIGINAL_TRUSTED_FORWARD=%q\n' "$WIFI_IFACE" "$UPSTREAM_IFACE" "$ORIGINAL_CONNECTION" "$ORIGINAL_FORWARDING" "$ORIGINAL_AP_ZONE" "$UPSTREAM_ZONE" "$ORIGINAL_UPSTREAM_MASQUERADE" "$ORIGINAL_TRUSTED_FORWARD" > "$STATE_DIR/state"
chmod 600 "$STATE_DIR/state"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cleanup_on_error() { echo "Startup failed; attempting rollback." >&2; "$SCRIPT_DIR/stop-campusnet-ap.sh" || true; }
trap cleanup_on_error ERR

nmcli device disconnect "$WIFI_IFACE" >/dev/null 2>&1 || true
nmcli device set "$WIFI_IFACE" managed no
ip link set "$WIFI_IFACE" down
ip addr flush dev "$WIFI_IFACE"
ip addr add "$AP_ADDRESS" dev "$WIFI_IFACE"
ip link set "$WIFI_IFACE" up

cat > "$STATE_DIR/dnsmasq.conf" <<EOF
interface=$WIFI_IFACE
bind-interfaces
listen-address=${AP_ADDRESS%/*}
dhcp-range=$DHCP_RANGE_START,$DHCP_RANGE_END,255.255.255.0,12h
dhcp-option=3,${AP_ADDRESS%/*}
dhcp-option=6,1.1.1.1,8.8.8.8
no-resolv
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

sysctl -w net.ipv4.ip_forward=1 >/dev/null
firewall-cmd --zone=trusted --add-interface="$WIFI_IFACE" >/dev/null
firewall-cmd --zone=trusted --add-forward >/dev/null
firewall-cmd --zone="$UPSTREAM_ZONE" --add-masquerade >/dev/null
nft -f - <<EOF
add table ip campusnet_demo
add chain ip campusnet_demo forward { type filter hook forward priority filter; policy accept; }
add chain ip campusnet_demo postrouting { type nat hook postrouting priority srcnat; policy accept; }
add rule ip campusnet_demo postrouting oifname "$UPSTREAM_IFACE" ip saddr 10.42.0.0/24 masquerade
EOF

dnsmasq --conf-file="$STATE_DIR/dnsmasq.conf"
hostapd -B -P "$STATE_DIR/hostapd.pid" -f "$STATE_DIR/hostapd.log" "$STATE_DIR/hostapd.conf"
trap - ERR
echo "CampusNet AP started: SSID=$AP_SSID interface=$WIFI_IFACE upstream=$UPSTREAM_IFACE"
echo "Connect a test phone, then inspect the dashboard and $STATE_DIR/hostapd.log."
