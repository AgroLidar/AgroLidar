from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class RegistryEntry:
    version: str
    timestamp: str
    status: str
    checkpoint: str
    config_hash: str
    dataset_manifest: str
    metrics: dict
    notes: str = ""


class ModelRegistry:
    def __init__(self, registry_dir: str | Path):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.registry_dir / "registry.json"
        if not self.registry_path.exists():
            self.registry_path.write_text("[]\n", encoding="utf-8")

    def list_entries(self) -> list[dict]:
        return json.loads(self.registry_path.read_text(encoding="utf-8"))

    def add(self, entry: RegistryEntry) -> dict:
        entries = self.list_entries()
        entries.append(asdict(entry))
        self.registry_path.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
        return asdict(entry)

    def latest_by_status(self, status: str) -> dict | None:
        entries = [item for item in self.list_entries() if item.get("status") == status]
        if not entries:
            return None
        return sorted(entries, key=lambda x: x["timestamp"])[-1]


def config_hash(config: dict) -> str:
    canonical = json.dumps(config, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:12]


def new_entry(version: str, status: str, checkpoint: str, config: dict, dataset_manifest: str, metrics: dict, notes: str = "") -> RegistryEntry:
    return RegistryEntry(
        version=version,
        timestamp=datetime.now(timezone.utc).isoformat(),
        status=status,
        checkpoint=checkpoint,
        config_hash=config_hash(config),
        dataset_manifest=dataset_manifest,
        metrics=metrics,
        notes=notes,
    )
