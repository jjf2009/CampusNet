"""Local RADIUS service health check.

Uses a bounded, argument-only ``systemctl is-active`` call. The service
name comes from configuration, never from request input, so there is no
shell injection surface.
"""

from __future__ import annotations

import shutil
import subprocess

_VALID_STATES = {"active", "inactive", "failed", "unknown"}


def radius_status(service_name: str) -> dict[str, str]:
    if not shutil.which("systemctl"):
        return {"status": "unknown", "service": service_name}
    try:
        proc = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"status": "unknown", "service": service_name}

    state = proc.stdout.strip()
    if state not in _VALID_STATES:
        state = "unknown"
    return {"status": state, "service": service_name}
