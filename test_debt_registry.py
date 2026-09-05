"""Tests for debt_registry.py — including the two production bugs that ate us.

Run: python -m pytest test_debt_registry.py -q
"""

from pathlib import Path

import pytest

from debt_registry import parse_debt_registry, render_gate_report

EXAMPLE = Path(__file__).parent / "example" / "debt-registry.md"


@pytest.fixture(scope="module")
def reg():
    out = parse_debt_registry(EXAMPLE)
    assert out["exists"] is True, out
    return out


def ids(entries):
    return [e["id"] for e in entries]


# ---- bucketing ----


def test_p0_active(reg):
    assert ids(reg["p0_active"]) == ["D-2026-09-05-014"]


def test_p1_active_excludes_inprogress_and_deferred(reg):
    """Status semantics bug (production): only strictly-open counts."""
    assert ids(reg["p1_active"]) == ["D-2026-09-05-003"]


def test_p2_active_excludes_done(reg):
    assert ids(reg["p2_active"]) == ["D-2026-09-05-004"]


def test_total_active(reg):
    assert reg["total_active"] == 3
    assert reg["p0_count"] == 1 and reg["p1_count"] == 1 and reg["p2_count"] == 1


def test_done_recent_from_history_section(reg):
    assert "D-2026-09-05-FIX1" in ids(reg["done_recent"])


def test_entry_shape(reg):
    e = reg["p0_active"][0]
    assert e["title"] == "sample P0 debt"
    assert e["p_grade"] == "P0"
    assert "demonstrates an active P0 debt" in e["problem"]
    assert e["status"].startswith("open")


# ---- freshness anchor (D-012) ----


def test_freshness_anchor(reg):
    assert reg["source_mtime_epoch"] == pytest.approx(EXAMPLE.stat().st_mtime, abs=1.0)
    assert reg["source_mtime_iso"][:10]  # ISO date prefix present
    assert reg["source_path"] == str(EXAMPLE)


# ---- the MULTILINE bug (production: ^ without re.M → empty parse) ----


def test_multiline_field_parsing():
    """Without re.MULTILINE on the field regex, NO entry gets fields parsed
    (only the string start matches ^). Lock the non-empty result."""
    reg = parse_debt_registry(EXAMPLE)
    assert reg["p1_active"][0]["problem"] != "(无)"
    assert reg["p1_active"][0]["status"] != "(无)"


# ---- robustness ----


def test_missing_file():
    out = parse_debt_registry(Path(__file__).parent / "nope.md")
    assert out["exists"] is False
    assert "not found" in out["reason"]


def test_empty_registry(tmp_path):
    f = tmp_path / "empty.md"
    f.write_text("# nothing here\n", encoding="utf-8")
    out = parse_debt_registry(f)
    assert out["exists"] is True and out["total_active"] == 0


def test_problem_truncation(tmp_path):
    f = tmp_path / "long.md"
    f.write_text(
        "## P1 — x\n### D-2026-01-01-001 — long\n- **问题**: " + "x" * 300 + "\n- **状态**: open\n",
        encoding="utf-8",
    )
    out = parse_debt_registry(f)
    assert out["p1_active"][0]["problem"].endswith("...")
    assert len(out["p1_active"][0]["problem"]) <= 153


def test_render_gate_report_is_user_visible_text(reg):
    report = render_gate_report(reg)
    assert "p0_active" in report and "D-2026-09-05-014" in report
    assert isinstance(report, str)  # plain text, fit for a reply body
