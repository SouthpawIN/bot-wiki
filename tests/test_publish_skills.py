"""Contract tests for fleet-skill publishing and the validator's skill count."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relpath: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


publish = load("publish_skills", "tools/publish_skills.py")
verify = load("verify_bots", "scripts/verify_bots.py")

BOT = """---
type: bot
slug: demo
name: Demo
status: active
---

**Mission.** Prove that a bot loader renders.

**Interface.** `skill: demo`.

## Skills

- `bots/demo/skills/repeat/SKILL.md`

## Loops

- `bots/demo/loops/daily.md`

**Hold points.** Never publish alone.

**Needs from the operator.** None.
"""

FLEET_SKILL = """---
name: shared-tool
description: The shared procedure both bots call.
version: 1.0.0
---

# shared tool
"""


def make_wiki(tmp_path: Path) -> Path:
    wiki = tmp_path / "wiki"
    (wiki / "bots/demo/skills/repeat").mkdir(parents=True)
    (wiki / "bots/demo/loops").mkdir(parents=True)
    (wiki / "bots/demo/BOT.md").write_text(BOT, encoding="utf-8")
    (wiki / "bots/demo/skills/repeat/SKILL.md").write_text(
        "---\nname: repeat\ndescription: x\n---\n", encoding="utf-8"
    )
    (wiki / "bots/demo/loops/daily.md").write_text(
        "---\nbot: demo\nschedule: daily\nstate: proposed\nskill: repeat\n---\n",
        encoding="utf-8",
    )
    (wiki / "bots/_fleet/skills/shared-tool").mkdir(parents=True)
    (wiki / "bots/_fleet/skills/shared-tool/SKILL.md").write_text(
        FLEET_SKILL, encoding="utf-8"
    )
    return wiki


def run(module, monkeypatch, argv: list[str]) -> int:
    monkeypatch.setattr(sys, "argv", [module.__file__, *argv])
    return module.main()


def test_publisher_installs_bot_and_fleet_skills(tmp_path: Path, monkeypatch):
    wiki = make_wiki(tmp_path)
    home = tmp_path / "home"
    assert run(publish, monkeypatch, [str(wiki), str(home)]) == 0
    assert (home / "skills/bots/demo/SKILL.md").is_file()
    fleet = home / "skills/fleet/shared-tool/SKILL.md"
    assert fleet.is_file()
    assert "name: shared-tool" in fleet.read_text(encoding="utf-8")
    # fleet skills keep their own name, never bot-<name>
    assert not (home / "skills/bots/shared-tool").exists()


def test_publisher_refuses_a_fleet_name_that_disagrees_with_its_folder(
    tmp_path: Path, monkeypatch, capsys
):
    wiki = make_wiki(tmp_path)
    (wiki / "bots/_fleet/skills/shared-tool/SKILL.md").write_text(
        "---\nname: other-name\ndescription: x\n---\n", encoding="utf-8"
    )
    assert run(publish, monkeypatch, [str(wiki), str(tmp_path / "home")]) == 1
    assert "!=" in capsys.readouterr().err


def test_validator_counts_fleet_skills_and_matches_publisher(tmp_path: Path):
    wiki = make_wiki(tmp_path)
    bot_skills, fleet_skills = verify.skill_counts(wiki)
    assert (bot_skills, fleet_skills) == (1, 1)

    home = tmp_path / "home"
    assert publish.main.__module__  # module loads
    original = sys.argv
    sys.argv = [publish.__file__, str(wiki), str(home)]
    try:
        assert publish.main() == 0
    finally:
        sys.argv = original
    installed = len(list(home.glob("skills/*/*/SKILL.md")))
    assert installed == bot_skills + fleet_skills
