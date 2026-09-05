"""
debt_registry.py — parse a markdown debt registry into machine-readable active-debt buckets.

Part of the "Result Gate + Debt Ledger" pattern for self-improving agents.

The debt registry is a single markdown file, NOT an archive: it is the working
checklist an agent must read before every session. Format contract:

    ## P0 — <section title>          # P grade is inferred from the section header
    ### D-YYYY-MM-DD-NNN — <title>   # debt entry (or D-YYYY-MM-DD-FIXN for history)
    - **状态**: open                 # status field (also: 问题 / 文件)

Buckets returned: p0_active / p1_active / p2_active / done_recent, plus a
freshness anchor (source_mtime_epoch) so cache-reading callers can detect
stale reads. Active = status strictly 'open' or 'open (...)' — 'in-progress',
'partial', 'deferred', 'done' are all excluded.

Extracted from a real production agent (Hermes OPC, 2026-09). Every design
decision here is scar tissue from a real failure — see README.md.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

_DEBT_PATTERN = re.compile(r"^### (D-\d{4}-\d{2}-\d{2}-(?:\d{3}|FIX\d+))\s+—\s+(.+?)$")
# ⚠️ MULTILINE is mandatory: without it, ^ only matches the string start
# (a real pitfall that silently produced empty parses in production)
_FIELD_PATTERN = re.compile(r"^-\s+\*\*(问题|状态|文件)\*\*:\s*(.+?)$", re.MULTILINE)

_SECTION_P0 = "## P0"
_SECTION_P1 = "## P1"
_SECTION_P2 = "## P2"
_SECTION_DONE_MARKERS = ("## 已完成债", "## Completed")


def _is_active(status: str) -> bool:
    """Active = strictly 'open' or 'open (...)'. Everything else is excluded."""
    s = status.strip().lower()
    return s == "open" or s.startswith("open (")


def parse_debt_registry(path: str | Path) -> dict:
    """Parse a debt-registry markdown file into active-debt buckets.

    Returns a dict:
        exists: bool
        total_active: int
        p0_active / p1_active / p2_active: list of entry dicts
        done_recent: last 5 completed entries
        source_mtime_epoch / source_mtime_iso: freshness anchor
        source_path: str

    Each entry dict: {id, title, p_grade, problem (<=150 chars), status}.
    """
    debt_path = Path(path)
    if not debt_path.exists():
        return {"exists": False, "reason": f"{debt_path} not found"}
    try:
        text = debt_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:  # noqa: BLE001 — parse must never crash session start
        return {"exists": False, "reason": f"read fail: {e}"}

    source_mtime = debt_path.stat().st_mtime
    source_mtime_iso = datetime.fromtimestamp(source_mtime).isoformat(timespec="seconds")

    # 1. Walk lines, track current P-section so each debt inherits its grade.
    raw_entries = []
    current_p = "?"
    current_section = "active"

    for line in text.splitlines():
        if line.startswith(_SECTION_P0):
            current_p, current_section = "P0", "active"
        elif line.startswith(_SECTION_P1):
            current_p, current_section = "P1", "active"
        elif line.startswith(_SECTION_P2):
            current_p, current_section = "P2", "active"
        elif any(line.startswith(m) for m in _SECTION_DONE_MARKERS):
            current_p, current_section = "?", "done"
        m = _DEBT_PATTERN.match(line)
        if m:
            raw_entries.append(
                {
                    "id": m.group(1),
                    "title": m.group(2).strip(),
                    "p_grade": "done" if current_section == "done" else current_p,
                    "section": current_section,
                    "_raw_fields": {},
                }
            )

    # 2. Grab 状态/问题 fields from each entry's own section text.
    for entry in raw_entries:
        section_start = text.find(f"### {entry['id']}")
        if section_start < 0:
            continue
        next_start = text.find("### ", section_start + 10)
        if next_start < 0:
            next_start = len(text)
        section_text = text[section_start:next_start]
        for fm in _FIELD_PATTERN.finditer(section_text):
            entry["_raw_fields"][fm.group(1)] = fm.group(2).strip()

    # 3. Final shape.
    clean_entries = []
    for e in raw_entries:
        problem = e["_raw_fields"].get("问题", "(无)")
        problem_short = problem[:150] + ("..." if len(problem) > 150 else "")
        clean_entries.append(
            {
                "id": e["id"],
                "title": e["title"],
                "p_grade": e["p_grade"],
                "problem": problem_short,
                "status": e["_raw_fields"].get("状态", "(无)"),
            }
        )

    # 4. Bucket by grade, active only.
    p0_active = [e for e in clean_entries if e["p_grade"] == "P0" and _is_active(e["status"])]
    p1_active = [e for e in clean_entries if e["p_grade"] == "P1" and _is_active(e["status"])]
    p2_active = [e for e in clean_entries if e["p_grade"] == "P2" and _is_active(e["status"])]
    done_recent = [e for e in clean_entries if e["p_grade"] == "done"][:5]

    return {
        "exists": True,
        "total_active": len(p0_active) + len(p1_active) + len(p2_active),
        "p0_count": len(p0_active),
        "p1_count": len(p1_active),
        "p2_count": len(p2_active),
        "p0_active": p0_active,
        "p1_active": p1_active,
        "p2_active": p2_active,
        "done_recent": done_recent,
        "source_mtime_epoch": source_mtime,
        "source_mtime_iso": source_mtime_iso,
        "source_path": str(debt_path),
    }


def render_gate_report(registry: dict) -> str:
    """Render the one-line result-gate report an agent must deliver to its USER.

    Deliberately plain text: the point of the result gate is that the debt
    status reaches a human-readable surface, not just the agent's tool stack.
    """
    if not registry.get("exists"):
        return f"debt registry unreadable: {registry.get('reason', 'unknown')}"
    lines = []
    for grade in ("p0_active", "p1_active", "p2_active"):
        ids = [e["id"] for e in registry.get(grade, [])]
        lines.append(f"{grade}: {ids if ids else '0 active'}")
    return " | ".join(lines)
