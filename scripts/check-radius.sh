#!/usr/bin/env bash
set -euo pipefail
service_name="${RADIUS_SERVICE_NAME:-radiusd}"
state="$(systemctl is-active "$service_name" 2>/dev/null || true)"
case "$state" in active|inactive|failed) echo "${service_name}: ${state}" ;; *) echo "${service_name}: unknown" ;; esac

