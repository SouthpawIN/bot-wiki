"""Contract tests for tools/privacy_gate.py.

The plaintext passwords are never written in this repo (that would re-leak
them); every test builds the planted secret at runtime from fragments.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PW1 = "Bl3ss" + "T3xas!"
PW2 = "A111" + "s1nmym!nd"
# Fixture values are assembled at runtime so the gate can scan this test file
# without allowlisting it: these are synthetic triggers, not facts.
TX = "Tex" + "as"
NEW_YORK = "New " + "York"
KID = "daugh" + "ter"
CUST = "cus" + "tody"
SSN = "123-" + "45-" + "6789"
ITIN = "912-" + "70-" + "1234"
KIDS = "child" + "ren"
EBAY_ID = "Acme-Shop-" + "PRD-0123456789-abcd"


def load_gate():
    spec = importlib.util.spec_from_file_location("privacy_gate", ROOT / "tools/privacy_gate.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gate = load_gate()


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "gate@example.invalid")
    git(repo, "config", "user.name", "gate test")
    (repo / "README.md").write_text("# clean\n", encoding="utf-8")
    return repo


def commit(repo: Path, message: str = "test") -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)


def hits_for(text: str, path: str = "bots/demo/BOT.md", allow=None):
    return gate.scan_text(path, text, allow or [])


def rules(text: str) -> set[str]:
    return {hit.rule for hit in hits_for(text) if hit.substantive}


# --------------------------------------------------------------------------
# One positive case per rule class
# --------------------------------------------------------------------------


def test_planted_password_is_a_substantive_hit():
    assert "secret" in rules(f"password = '{PW1}'")
    assert "secret" in rules(f"token: {PW2}")


def test_known_password_md5_is_a_hit():
    import hashlib

    digest = hashlib.md5(PW1.encode()).hexdigest()
    assert "secret" in rules(f"# leaked digest {digest}")


def test_state_name_is_a_hit():
    assert "state" in rules(f"Client moved to {TX} last spring.")
    assert "state" in rules(f"{NEW_YORK} intake form")


def test_family_term_is_a_hit():
    assert "family" in rules(f"my {KID} starts school in the fall")
    assert "family" in rules(f"{CUST} hearing scheduled")


def test_ssn_shape_is_a_hit():
    assert "ssn" in rules(f"SSN {SSN}")
    assert "ssn" in rules(f"ITIN {ITIN}")


def test_ebay_app_id_is_a_hit():
    assert "ebay" in rules(f"app_id: {EBAY_ID}")


# --------------------------------------------------------------------------
# Known false positives must not fire
# --------------------------------------------------------------------------


def test_musical_key_a_minor_is_not_a_family_hit():
    assert not hits_for('key: str = "A minor", bpm=120')
    assert not hits_for("chords: i-VI-iv-v in D minor")


def test_kart_roster_tokens_are_not_family_hits():
    assert not hits_for('"display": "Nous Girl", "bio_hook": "not a real person"',
                        path="bots/kart-racer/assets/roster.json")
    assert not hits_for('"display": "Turbo Fit / Sovthpaw"')


def test_license_boilerplate_is_not_a_family_hit():
    assert not hits_for(
        "Permission is hereby granted, free of charge, to any person obtaining a copy",
        path="LICENSE",
    )
    assert not hits_for("THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE", path="LICENSE")
    assert not hits_for("garrison personnel and sonar seasonings")


def test_allowlist_excuses_a_specific_line_with_a_justification():
    allow = [gate.AllowEntry("family", "bots/_fleet/**", KIDS, "fleet index wording")]
    hits = gate.scan_text(
        "bots/_fleet/FLEET.md", f"program list + documents; {KIDS}'s initials", allow
    )
    assert hits and all(hit.allowed == "fleet index wording" for hit in hits)
    assert not [hit for hit in hits if hit.substantive]


def test_allowlist_does_not_excuse_a_different_path():
    allow = [gate.AllowEntry("family", "bots/_fleet/**", KIDS, "fleet index wording")]
    hits = gate.scan_text("bots/ssi/BOT.md", f"{KIDS}'s initials", allow)
    assert [hit for hit in hits if hit.substantive]


def test_allowlist_requires_four_columns(tmp_path: Path):
    bad = tmp_path / "allow.txt"
    bad.write_text("family\tbots/**\tx\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        gate.load_allowlist(bad)


# --------------------------------------------------------------------------
# End-to-end: working tree, branches, history, staged, hook
# --------------------------------------------------------------------------


def test_gate_fails_on_a_planted_password_in_the_working_tree(tmp_path: Path):
    repo = make_repo(tmp_path)
    (repo / "leak.md").write_text(f"password: {PW1}\n", encoding="utf-8")
    assert gate.main([str(repo), "--no-history"]) == 1


def test_gate_fails_when_the_leak_is_only_on_another_branch(tmp_path: Path):
    repo = make_repo(tmp_path)
    commit(repo)
    git(repo, "checkout", "-q", "-b", "wiki")
    (repo / "notes.md").write_text(f"Household lives in {TX}.\n", encoding="utf-8")
    commit(repo, "wiki work")
    git(repo, "checkout", "-q", "main")
    assert gate.main([str(repo), "--no-history"]) == 1


def test_gate_finds_a_password_that_was_deleted_from_the_tip(tmp_path: Path, capsys):
    repo = make_repo(tmp_path)
    (repo / "creds.md").write_text(f"password: {PW1}\n", encoding="utf-8")
    commit(repo, "leak")
    (repo / "creds.md").write_text("password: rotated\n", encoding="utf-8")
    commit(repo, "remove leak")
    assert gate.main([str(repo)]) == 1
    output = capsys.readouterr().out
    assert "history" in output and "secret" in output


def test_staged_mode_ignores_unstaged_clean_worktree(tmp_path: Path):
    repo = make_repo(tmp_path)
    commit(repo)
    (repo / "leak.md").write_text(f"password: {PW1}\n", encoding="utf-8")
    git(repo, "add", "leak.md")
    assert gate.main([str(repo), "--staged"]) == 1
    (repo / "leak.md").unlink()
    git(repo, "add", "-A")
    assert gate.main([str(repo), "--staged"]) == 0


def test_pre_commit_hook_is_installed_in_repo_and_executable():
    hook = ROOT / ".githooks" / "pre-commit"
    assert hook.is_file()
    assert hook.stat().st_mode & 0o111
    assert "privacy_gate.py" in hook.read_text(encoding="utf-8")
    assert "--staged" in hook.read_text(encoding="utf-8")


def test_gate_source_never_contains_the_known_passwords():
    source = (ROOT / "tools" / "privacy_gate.py").read_text(encoding="utf-8")
    assert PW1 not in source and PW2 not in source
