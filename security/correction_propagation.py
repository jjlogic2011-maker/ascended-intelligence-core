"""Deterministic correction propagation and closure verification."""

from __future__ import annotations

import hashlib
import json
import uuid

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


SCHEMA_VERSION = "correction-propagation.v0.1"


def required_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def canonical_hash(value: object) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class CorrectionState(str, Enum):
    DISCOVERED = "DISCOVERED"
    NOTIFIED = "NOTIFIED"
    REASSESSMENT_REQUIRED = "REASSESSMENT_REQUIRED"
    REASSESSED_UNCHANGED = "REASSESSED_UNCHANGED"
    REPAIRED = "REPAIRED"
    QUARANTINED = "QUARANTINED"
    EXEMPT = "EXEMPT"
    UNRESOLVED = "UNRESOLVED"


TERMINAL = frozenset({
    CorrectionState.REASSESSED_UNCHANGED,
    CorrectionState.REPAIRED,
    CorrectionState.QUARANTINED,
    CorrectionState.EXEMPT,
})


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    material: bool = True


class LineageGraph:
    def __init__(self) -> None:
        self._edges: dict[str, list[Edge]] = {}

    def add_edge(
        self,
        source: str,
        target: str,
        material: bool = True,
    ) -> None:
        source = required_text(source, "source")
        target = required_text(target, "target")

        if not isinstance(material, bool):
            raise ValueError("material must be a boolean")

        existing = self._edges.setdefault(source, [])

        for edge in existing:
            if edge.target == target:
                if edge.material != material:
                    raise ValueError("Conflicting edge classification")
                return

        existing.append(Edge(source, target, material))

    def descendants(self, origin: str) -> list[str]:
        origin = required_text(origin, "origin")
        seen = {origin}
        queue = deque([origin])
        result = []

        while queue:
            current = queue.popleft()

            for edge in sorted(
                self._edges.get(current, []),
                key=lambda item: item.target,
            ):
                if not edge.material:
                    continue

                if edge.target in seen:
                    continue

                seen.add(edge.target)
                result.append(edge.target)
                queue.append(edge.target)

        return result

    @property
    def snapshot_sha256(self) -> str:
        rows = [
            {
                "source": edge.source,
                "target": edge.target,
                "material": edge.material,
            }
            for edges in self._edges.values()
            for edge in edges
        ]

        rows.sort(
            key=lambda row: (
                row["source"],
                row["target"],
                row["material"],
            )
        )

        return canonical_hash(rows)


@dataclass
class Correction:
    correction_id: str
    origin: str
    reason: str
    timestamp: str
    graph_sha256: str
    _dispositions: dict[str, CorrectionState] = field(
        default_factory=dict,
        repr=False,
    )

    @property
    def dispositions(self) -> dict[str, CorrectionState]:
        return dict(self._dispositions)

    def to_record(self) -> dict:
        body = {
            "schema_version": SCHEMA_VERSION,
            "correction_id": self.correction_id,
            "origin": self.origin,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "graph_sha256": self.graph_sha256,
            "affected_nodes": sorted(self._dispositions),
            "dispositions": {
                node: state.value
                for node, state in sorted(self._dispositions.items())
            },
        }

        return {
            **body,
            "snapshot_sha256": canonical_hash(body),
        }


class CorrectionRegistry:
    def __init__(self) -> None:
        self._corrections: dict[str, Correction] = {}

    def register(
        self,
        graph: LineageGraph,
        origin: str,
        reason: str,
        correction_id: Optional[str] = None,
    ) -> Correction:
        if not isinstance(graph, LineageGraph):
            raise TypeError("graph must be a LineageGraph")

        origin = required_text(origin, "origin")
        reason = required_text(reason, "reason")
        cid = required_text(
            correction_id or str(uuid.uuid4()),
            "correction_id",
        )

        if cid in self._corrections:
            raise ValueError(f"Correction already registered: {cid}")

        correction = Correction(
            correction_id=cid,
            origin=origin,
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
            graph_sha256=graph.snapshot_sha256,
            _dispositions={
                node: CorrectionState.DISCOVERED
                for node in graph.descendants(origin)
            },
        )

        self._corrections[cid] = correction
        return correction

    def notify(self, correction_id: str) -> Correction:
        correction = self._get(correction_id)

        for node, state in list(correction._dispositions.items()):
            if state == CorrectionState.DISCOVERED:
                correction._dispositions[node] = CorrectionState.NOTIFIED

        return correction

    def require_reassessment(self, correction_id: str) -> Correction:
        correction = self._get(correction_id)

        for node, state in list(correction._dispositions.items()):
            if state == CorrectionState.NOTIFIED:
                correction._dispositions[node] = (
                    CorrectionState.REASSESSMENT_REQUIRED
                )

        return correction

    def propagate(self, correction_id: str) -> Correction:
        self.notify(correction_id)
        return self.require_reassessment(correction_id)

    def set_disposition(
        self,
        correction_id: str,
        node: str,
        state: CorrectionState,
    ) -> None:
        correction = self._get(correction_id)
        node = required_text(node, "node")

        if node not in correction._dispositions:
            raise ValueError(f"Unknown affected node: {node}")

        if not isinstance(state, CorrectionState):
            raise TypeError("state must be CorrectionState")

        if state not in TERMINAL and state != CorrectionState.UNRESOLVED:
            raise ValueError("Invalid disposition")

        current = correction._dispositions[node]

        if current != CorrectionState.REASSESSMENT_REQUIRED:
            raise ValueError(
                f"Node must be reassessment-ready; current state: {current}"
            )

        correction._dispositions[node] = state

    def reopen_unresolved(self, correction_id: str, node: str) -> None:
        correction = self._get(correction_id)
        node = required_text(node, "node")

        if node not in correction._dispositions:
            raise ValueError(f"Unknown affected node: {node}")

        if correction._dispositions[node] != CorrectionState.UNRESOLVED:
            raise ValueError("Only unresolved nodes can be reopened")

        correction._dispositions[node] = (
            CorrectionState.REASSESSMENT_REQUIRED
        )

    def verify_closure(
        self,
        correction_id: str,
    ) -> tuple[bool, list[tuple[str, CorrectionState]]]:
        correction = self._get(correction_id)

        open_nodes = [
            (node, state)
            for node, state in sorted(
                correction._dispositions.items()
            )
            if state not in TERMINAL
        ]

        return len(open_nodes) == 0, open_nodes

    def _get(self, correction_id: str) -> Correction:
        if correction_id not in self._corrections:
            raise KeyError(f"Unknown correction: {correction_id}")
        return self._corrections[correction_id]
