import subprocess
from typing import Any


def radius_status(service_name: str) -> dict[str, Any]:
    try:
        result = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True, timeout=2, check=False)
        state = result.stdout.strip()
        return {"status": state if state in {"active", "inactive", "failed", "unknown"} else "unknown", "service": service_name}
    except (OSError, subprocess.TimeoutExpired):
        return {"status": "unknown", "service": service_name}

