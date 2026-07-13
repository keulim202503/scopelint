import json
from dataclasses import asdict, dataclass
from pathlib import Path

from scopelint.checker import ScopeFinding


@dataclass(frozen=True)
class HistoryEntry:
    timestamp: str
    task: str
    ok: bool
    findings: list[ScopeFinding]


def _entry_to_dict(entry: HistoryEntry) -> dict:
    return {
        "timestamp": entry.timestamp,
        "task": entry.task,
        "ok": entry.ok,
        "findings": [asdict(f) for f in entry.findings],
    }


def _dict_to_entry(data: dict) -> HistoryEntry:
    return HistoryEntry(
        timestamp=data["timestamp"],
        task=data["task"],
        ok=data["ok"],
        findings=[ScopeFinding(path=f["path"], reason=f["reason"]) for f in data["findings"]],
    )


def record_result(log_path: str, entry: HistoryEntry) -> None:
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(_entry_to_dict(entry), ensure_ascii=False) + "\n")


def load_history(log_path: str) -> list[HistoryEntry]:
    path = Path(log_path)
    if not path.exists():
        return []
    entries = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(_dict_to_entry(json.loads(line)))
    return entries
