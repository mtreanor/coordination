"""An append-only JSONL log of every decision: what was asked and what came back."""

import json
from datetime import UTC, datetime
from pathlib import Path

from .decision import Decision, DecisionRequest


class DecisionLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, request: DecisionRequest, decision: Decision, **context) -> None:
        record = {
            "time": datetime.now(UTC).isoformat(),
            **context,
            "request": request.model_dump(),
            "decision": decision.model_dump(),
        }
        with self.path.open("a") as f:
            f.write(json.dumps(record) + "\n")
