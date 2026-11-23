"""Tests for the Folio resume workbench. All fixtures are synthetic."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import resume as R  # noqa: E402

CLEAN = """# Dana Q. Sample
Sampleville, TX · dana@example.com · (555) 010-0100

## Professional Summary
Bartender and trainer with 12 years in high-volume restaurants, TABC-certified,
and experienced running a 60-seat bar and a 9-person front-of-house team.

## Core Skills
- Cocktail program design · TABC · ServSafe · Toast POS · staff training

## Experience

### Head Bartender — Sample Grill, Sampleville, TX
*2020 – 2024*
- Cut pour cost from 24% to 19% by rewriting the 32-item cocktail menu and re-spec'ing every well.
- Trained 18 new servers and bartenders, certifying all of them on a 40-point service standard.

### Server — Sample Grill, Sampleville, TX
*2016 – 2020*
- Carried a 12-table section with a 4.8/5 guest survey average across 900 reviews.
"""

BROKEN = """# Dana Q. Sample
412 Sample Lane
Sampleville, TX 77316
dana@example.com

## Objective
I am a passionate, hard worker and a team player who would be excited to join the team.

## Experience

### Server — Sample Grill, Sampleville, TX
*2016 – 2020*
- I was responsible for taking orders and helping with guests.
- Provided excellent customer service.

### Head Bartender — Sample Grill, Sampleville, TX
*2020 – 2024*
- Managed the bar.

### Stay at Home Mom — Household
*2012 – 2016*
- Managed household schedules and provided administrative support for a small business.

## References
References available upon request.
"""


def test_parse_roles_and_dates():
    res = R.parse(CLEAN)
    assert res.name == "Dana Q. Sample"
    assert [r.title for r in res.roles] == ["Head Bartender", "Server"]
    assert res.roles[0].employer == "Sample Grill"
    assert res.roles[0].location == "Sampleville, TX"
    assert res.roles[0].start == 2020 and res.roles[0].end == 2024
    assert len(res.roles[0].bullets) == 2
    assert res.skills and "TABC" in res.skills[0]


def test_current_role_flag():
    res = R.parse(CLEAN.replace("*2020 – 2024*", "*2020 – Present*"))
    assert res.roles[0].current is True
    assert res.roles[0].end is None


def test_clean_resume_has_no_errors():
    errors = [f for f in R.lint(R.parse(CLEAN)) if f["level"] == "error"]
    assert errors == []


def test_street_address_is_an_error():
    codes = {f["code"] for f in R.lint(R.parse(BROKEN))}
    assert "street-address" in codes


def test_first_person_and_duty_openers():
    codes = {f["code"] for f in R.lint(R.parse(BROKEN))}
    assert "first-person" in codes
    assert "duty-opener" in codes


def test_unquantified_bullets_are_reported_without_inventing_numbers():
    res = R.parse(BROKEN)
    findings = R.lint(res)
    assert any(f["code"] == "no-metric" for f in findings)
    # the text itself is untouched: lint reports, it does not fill
    assert "I was responsible for taking orders" in res.roles[0].bullets[0].text


def test_date_order_and_duplicate_employer():
    codes = {f["code"] for f in R.lint(R.parse(BROKEN))}
    assert "date-order" in codes
    assert "duplicate-employer" in codes


def test_homemaker_and_references_flags():
    codes = {f["code"] for f in R.lint(R.parse(BROKEN))}
    assert "homemaker-title" in codes
    assert "references-line" in codes


def test_cliches_flagged():
    codes = {f["code"] for f in R.lint(R.parse(BROKEN))}
    assert "cliche" in codes


def test_ledger_marks_missing_metrics():
    ledger = R.ledger(R.parse(BROKEN))
    assert "[[CONFIRM: metric]]" in ledger
    assert "Sample Grill" in ledger
    assert "| Role | Employer | Dates | Bullets | Quantified |" in ledger


def test_keywords_coverage():
    posting = ("Bartender needed. Must hold a current TABC certification and know "
               "cocktail recipes. Banquet experience preferred. Inventory and cost control "
               "duties. Banquet service for private events.")
    report = R.keywords(R.parse(CLEAN).text(), posting)
    assert "TABC" in posting and "tabc" in report["covered"]
    assert "banquet" in report["missing"]
    assert 0.0 <= report["coverage"] <= 1.0


def test_render_docx(tmp_path: Path):
    pytest.importorskip("docx")
    out = R.render_docx(R.parse(CLEAN), tmp_path / "out.docx")
    assert out.exists() and out.stat().st_size > 3000


def test_cli_lint_exit_codes(tmp_path: Path):
    script = Path(__file__).resolve().parents[1] / "scripts" / "resume.py"
    dirty = tmp_path / "dirty.md"
    dirty.write_text(BROKEN, encoding="utf-8")
    clean = tmp_path / "clean.md"
    clean.write_text(CLEAN, encoding="utf-8")
    bad = subprocess.run([sys.executable, str(script), "lint", str(dirty), "--json"],
                         capture_output=True, text=True)
    assert bad.returncode == 1
    payload = json.loads(bad.stdout)
    assert payload["errors"] > 0
    good = subprocess.run([sys.executable, str(script), "lint", str(clean)],
                          capture_output=True, text=True)
    assert good.returncode == 0
