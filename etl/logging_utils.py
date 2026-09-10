from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG_PATH = PROJECT_ROOT / "data" / "staging" / "transformation_log.jsonl"


def log_transformation(
    step: str,
    status: str,
    details: dict[str, Any] | None = None,
    log_path: Path = DEFAULT_LOG_PATH,
) -> None:
    """Append one transformation/audit event as JSONL."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "step": step,
        "status": status,
        "details": details or {},
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
