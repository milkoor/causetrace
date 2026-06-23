"""Experimental-unit projection for corpus records."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExperimentalUnit:
    """A session projected into CRDD comparison dimensions."""

    session_id: str
    metadata: dict[str, Any]
    metadata_provenance: dict[str, str]
    stats: dict[str, Any]
    topology: str

    @property
    def runtime(self) -> str:
        return str(self.metadata.get("runtime") or "")

    @property
    def task_type(self) -> str:
        return str(self.metadata.get("task_type") or "")

    @property
    def task_source(self) -> str:
        return str(self.metadata.get("task_source") or "")

    @property
    def data_origin(self) -> str:
        return str(self.metadata.get("data_origin") or "")

    @property
    def intervention_lane(self) -> str:
        return str(self.metadata.get("intervention_lane") or "")

    @property
    def success(self) -> bool | None:
        value = self.metadata.get("success")
        return value if isinstance(value, bool) else None

    @property
    def human_intervention(self) -> bool | None:
        value = self.metadata.get("human_intervention")
        return value if isinstance(value, bool) else None

    @property
    def event_count(self) -> int:
        return int(self.stats.get("event_count", 0) or 0)

    def has_fields(self, fields: tuple[str, ...]) -> bool:
        return all(self.metadata.get(field) not in (None, "", [], {}) for field in fields)

    def to_manifest_record(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "runtime": self.runtime,
            "task_type": self.task_type,
            "task_source": self.task_source,
            "data_origin": self.data_origin,
            "intervention_lane": self.intervention_lane,
            "success": self.success,
            "human_intervention": self.human_intervention,
            "topology": self.topology,
            "event_count": self.event_count,
        }


def record_to_unit(record: dict[str, Any]) -> ExperimentalUnit:
    """Build an experimental unit from a corpus record."""
    return ExperimentalUnit(
        session_id=str(record["session_id"]),
        metadata=dict(record.get("metadata", {})),
        metadata_provenance=dict(record.get("metadata_provenance", {})),
        stats=dict(record.get("stats", {})),
        topology=str(record.get("topology") or ""),
    )
