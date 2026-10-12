"""
Diagram & Markup Agent — produces supporting diagrams and structured markup.

Diagrams and markups are SUPPORTING artifacts only.
They never substitute for working functionality or verified evidence.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from research_lab.agents.evidence.ledger import append_evidence

DIAGRAM_DIR = Path(__file__).resolve().parents[2] / "evidence_logs" / "diagrams"
DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)


def generate_architecture_markup(
    title: str,
    components: List[str],
    flows: List[str],
    *,
    note: str = "Supporting diagram only — not a claim of operational deployment.",
) -> Dict[str, Any]:
    """Generate a simple Mermaid-style architecture markup and log it."""
    lines = ["```mermaid", "flowchart TD"]
    for i, c in enumerate(components):
        safe = c.replace('"', "'")
        lines.append(f'  C{i}["{safe}"]')
    for f in flows:
        lines.append(f"  {f}")
    lines.append("```")
    markup = "\n".join(lines)

    out_path = DIAGRAM_DIR / f"arch_{abs(hash(title)) % 10**8}.md"
    content = f"# {title}\n\n{note}\n\n{markup}\n"
    out_path.write_text(content, encoding="utf-8")

    entry = append_evidence(
        agent="DiagramMarkupAgent",
        action="generate_architecture_markup",
        claim=f"Architecture markup generated: {title}",
        classification="OPERATIONAL",
        evidence_type="diagram",
        payload={
            "title": title,
            "path": str(out_path),
            "component_count": len(components),
            "note": note,
        },
        status="recorded",
    )
    return {
        "title": title,
        "path": str(out_path),
        "markup_preview": markup[:500],
        "entry_id": entry.entry_id,
        "note": note,
    }


def generate_claim_table_markup(claims: List[Dict[str, str]]) -> str:
    """Produce a markdown table of validated claims for reports."""
    header = "| Claim | Classification | Working? | Limitations |\n|-------|----------------|----------|-------------|