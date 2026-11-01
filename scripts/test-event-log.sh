#!/usr/bin/env bash
set -euo pipefail
log_path="${RADIUS_EVENT_LOG:-backend/data/radius-events.jsonl}"
test -f "$log_path" || { echo "Event log not found: $log_path" >&2; exit 1; }
python3 - "$log_path" <<'PY'
import json, sys
path = sys.argv[1]
events = []
with open(path, encoding="utf-8") as stream:
    for line in stream:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if value.get("result") in {"accept", "reject"}:
            events.append(value["result"])
print(f"safe authentication events: {len(events)} (accept={events.count('accept')}, reject={events.count('reject')})")
PY
