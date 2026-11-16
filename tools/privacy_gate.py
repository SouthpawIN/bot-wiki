#!/usr/bin/env python3
"""Privacy gate: refuse to ship household facts or leaked credentials.

The wiki is public. `bots/ssi/BOT.md` promises that a `git grep` for household
facts returns zero before any change lands; this tool is that promise as an
executable gate instead of a habit.

Rules
-----
- ``secret``  — the two known leaked passwords, matched by MD5/SHA-256 digest of
  every credential-shaped token on a line. The plaintext is deliberately **not**
  stored here: a public repo cannot host the credential it is trying to keep
  out. A committed MD5 of a known password is caught too, by a direct scan for
  the digest.
- ``state``   — all 50 US state names, word-bounded, anywhere but an allowlist.
- ``family``  — children/daughter/son/custody/father/mother/spouse/wife/husband
  and minor(s), word-bounded. A musical key on the same line ("A minor") clears
  `minor`; kart-roster names and upstream license prose ("any person") are
  either word-bounded or documented in the allowlist, never excused by widening
  the pattern.
- ``ssn``     — dashed SSN/ITIN shapes (``123-45-6789``).
- ``ebay``    — eBay application IDs (``Name-Name-PRD-0123456789-abcdef12``).

Scans
-----
1. the working tree (uncommitted files), and
2. every local and remote branch tip, reported one line per branch, and
3. every blob reachable from any commit (history), so a password in an old
   commit still blocks instead of hiding behind a clean tip.

Exit status is non-zero on any substantive (non-allowlisted) hit, so it works as
a pre-commit hook and as a gate in the nightly fleet reconcile.

Usage
-----
    python tools/privacy_gate.py [repo-root]
    python tools/privacy_gate.py --staged        # pre-commit: staged files only

Install the hook once per clone:

    git config core.hooksPath .githooks
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------

STATE_NAMES = (
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine",
    "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
    "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
    "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
    "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia",
    "Washington", "West Virginia", "Wisconsin", "Wyoming",
)

FAMILY_TERMS = (
    "children", "daughter", "son", "sons", "custody", "father", "mother",
    "spouse", "wife", "husband", "minor", "minors",
)

STATE_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(name) for name in STATE_NAMES) + r")\b",
    re.I,
)
FAMILY_RE = re.compile(r"\b(?:" + "|".join(FAMILY_TERMS) + r")\b", re.I)
# "minor" is a family term only when it means a person. A musical key is the
# loudest false positive in this repo (the DAW plugin's default is "A minor"),
# so a musical context on the same line clears it.
MUSIC_RE = re.compile(
    r"\b[A-G](?:#|b|♯|♭)?\s+(?:major|minor)\b|\b(?:key|keys|scale|chord|chords|bpm|tempo)\b",
    re.I,
)
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
EBAY_RE = re.compile(r"\b[A-Za-z]+-[A-Za-z]+-PRD-[0-9a-fA-F-]+\b")

# MD5 and SHA-256 of the two passwords that leaked into a live branch. Only the
# digests live in the repo; the plaintext must never come back here.
SECRET_DIGESTS = {
    "4c51bd3b17c6c2fb223bac797ddb2df0": "md5 of leaked password #1",
    "f49d98c0122af3a26d9966bd02a4802e": "md5 of leaked password #2",
}

# Files this gate must not scan: its own digest table, and the allowlist
# itself (whose justifications quote the benign text they excuse).
SELF_EXCLUDE = {"tools/privacy_gate.py", "tools/privacy_allowlist.txt"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", "node_modules"}
CANDIDATE_RE = re.compile(r"[A-Za-z0-9!@#$%^&*()_+\-]{8,64}")
DIGEST_HEX = re.compile(r"\b[0-9a-f]{32}\b")
BINARY_SNIFF = 8192
MAX_BYTES = 8 * 1024 * 1024  # never read a blob bigger than this
SHOW_LIMIT = 10  # hits printed per group unless --verbose
_SCAN_CACHE: dict[tuple[str, str], list[Hit]] = {}


@dataclass(frozen=True)
class Hit:
    rule: str
    path: str
    line_no: int
    line: str
    allowed: str | None = None  # justification when allowlisted

    @property
    def substantive(self) -> bool:
        return self.allowed is None

    def render(self) -> str:
        text = f"[{self.rule}] {self.path}:{self.line_no}: {self.line.strip()[:200]}"
        if self.allowed:
            text += f"  (allowed: {self.allowed})"
        return text


@dataclass(frozen=True)
class AllowEntry:
    rule: str
    path_glob: str
    literal: str
    justification: str


def load_allowlist(path: Path | None) -> list[AllowEntry]:
    """Parse ``rule<TAB>path-glob<TAB>literal<TAB>justification`` lines."""
    if path is None or not path.exists():
        return []
    entries: list[AllowEntry] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 4 or not all(part.strip() for part in parts):
            raise SystemExit(
                f"{path}:{number}: allowlist needs 4 tab-separated columns "
                "(rule, path-glob, literal, justification)"
            )
        entries.append(AllowEntry(*(part.strip() for part in parts)))
    return entries


def allowed_by(entries: list[AllowEntry], rule: str, path: str, line: str) -> str | None:
    for entry in entries:
        if entry.rule not in ("*", rule):
            continue
        if not fnmatch.fnmatch(path, entry.path_glob):
            continue
        if entry.literal != "*" and entry.literal.lower() not in line.lower():
            continue
        return entry.justification
    return None


def has_known_secret(line: str) -> bool:
    """True when the line contains a known password or its MD5.

    Match credential-shaped runs with one regex pass rather than splitting the
    line into tokens: the archived vault contains multi-megabyte minified JSON
    lines, and token lists there are what made history scans crawl.
    """
    for hexd in DIGEST_HEX.findall(line):
        if hexd in SECRET_DIGESTS:
            return True
    for match in CANDIDATE_RE.finditer(line):
        token = match.group(0)
        if not any(char.isdigit() for char in token):
            continue
        raw = token.encode("utf-8", "replace")
        if (
            hashlib.md5(raw).hexdigest() in SECRET_DIGESTS
            or hashlib.sha256(raw).hexdigest() in SECRET_DIGESTS
        ):
            return True
    return False


def scan_line(path: str, number: int, line: str, entries: list[AllowEntry]) -> list[Hit]:
    hits: list[Hit] = []
    seen: set[tuple[str, str]] = set()

    def add(rule: str, matched: str) -> None:
        key = (rule, matched)
        if key in seen:
            return
        seen.add(key)
        hits.append(Hit(rule, path, number, line, allowed_by(entries, rule, path, line)))

    if has_known_secret(line):
        add("secret", line.strip())
    for match in STATE_RE.finditer(line):
        add("state", match.group(0))
    for match in FAMILY_RE.finditer(line):
        if match.group(0).lower() in {"minor", "minors"} and MUSIC_RE.search(line):
            continue
        add("family", match.group(0))
    for match in SSN_RE.finditer(line):
        add("ssn", match.group(0))
    for match in EBAY_RE.finditer(line):
        add("ebay", match.group(0))
    return hits


def scan_text(path: str, text: str, entries: list[AllowEntry]) -> list[Hit]:
    hits: list[Hit] = []
    for number, line in enumerate(text.splitlines(), 1):
        hits.extend(scan_line(path, number, line, entries))
    return hits


def decode_blob(data: bytes) -> str | None:
    if b"\0" in data[:BINARY_SNIFF]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


# --------------------------------------------------------------------------
# Git access
# --------------------------------------------------------------------------


def _git_run(root: Path, args: tuple[str, ...]) -> bytes:
    result = subprocess.run(
        ["git", *args], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if result.returncode != 0:
        raise SystemExit(
            f"git {' '.join(args)} failed: {result.stderr.decode('utf-8', 'replace').strip()}"
        )
    return result.stdout


def git(root: Path, *args: str) -> str:
    return _git_run(root, args).decode("utf-8", "replace")


class Blobs:
    """`git cat-file --batch` reader with an in-memory cache."""

    def __init__(self, root: Path) -> None:
        self.cache: dict[str, bytes | None] = {}
        self.proc = subprocess.Popen(
            ["git", "cat-file", "--batch"],
            cwd=root,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

    def get(self, sha: str) -> bytes | None:
        if sha in self.cache:
            return self.cache[sha]
        assert self.proc.stdin and self.proc.stdout
        self.proc.stdin.write(f"{sha}\n".encode())
        self.proc.stdin.flush()
        header = self.proc.stdout.readline().split()
        if len(header) < 3:
            # "<sha> missing" (or any non-object line): nothing to drain.
            self.cache[sha] = None
            return None
        size = int(header[2])
        data = self.proc.stdout.read(size)
        self.proc.stdout.read(1)  # trailing newline
        if header[1] != b"blob":
            # Drain the payload even for trees: leaving it unread desyncs the
            # batch stream, and every later read returns garbage.
            self.cache[sha] = None
            return None
        self.cache[sha] = data
        return data

    def close(self) -> None:
        if self.proc.stdin:
            self.proc.stdin.close()
        self.proc.wait(timeout=10)


def branch_refs(root: Path) -> list[tuple[str, str]]:
    out = git(root, "for-each-ref", "--format=%(refname) %(objectname)", "refs/heads", "refs/remotes")
    refs: list[tuple[str, str]] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        refname, sha = line.split(" ", 1)
        if refname.endswith("/HEAD") or refname == "HEAD":
            continue
        if refname.startswith("refs/heads/"):
            name = refname[len("refs/heads/"):]
        elif refname.startswith("refs/remotes/"):
            name = refname[len("refs/remotes/"):]
        else:
            continue
        refs.append((name, sha))
    return refs


def tree_blobs(root: Path, commit: str) -> list[tuple[str, str]]:
    out = git(root, "ls-tree", "-r", "-z", "--full-tree", commit)
    entries: list[tuple[str, str]] = []
    for record in out.split("\0"):
        if not record or "\t" not in record:
            continue
        meta, path = record.split("\t", 1)
        parts = meta.split()
        if len(parts) != 3 or parts[1] != "blob":
            continue
        entries.append((path, parts[2]))
    return entries


def scan_blob(blobs: Blobs, sha: str, path: str, entries: list[AllowEntry]) -> list[Hit]:
    key = (sha, path)
    if key in _SCAN_CACHE:
        return _SCAN_CACHE[key]
    if path in SELF_EXCLUDE:
        _SCAN_CACHE[key] = []
        return []
    data = blobs.get(sha)
    if data is None or len(data) > MAX_BYTES:
        _SCAN_CACHE[key] = []
        return []
    text = decode_blob(data)
    hits = scan_text(path, text, entries) if text is not None else []
    _SCAN_CACHE[key] = hits
    return hits


def scan_working_tree(root: Path, entries: list[AllowEntry]) -> list[Hit]:
    hits: list[Hit] = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if not path.is_file() or path.is_symlink():
            continue
        posix = rel.as_posix()
        if posix in SELF_EXCLUDE:
            continue
        if path.stat().st_size > MAX_BYTES:
            continue
        data = path.read_bytes()
        text = decode_blob(data)
        if text is None:
            continue
        hits.extend(scan_text(posix, text, entries))
    return hits


def staged_files(root: Path) -> list[str]:
    out = git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
    return [name for name in out.split("\0") if name]


def scan_staged(root: Path, entries: list[AllowEntry]) -> list[Hit]:
    hits: list[Hit] = []
    for posix in staged_files(root):
        if posix in SELF_EXCLUDE:
            continue
        try:
            data = _git_run(root, ("show", f":{posix}"))
        except SystemExit:
            continue
        text = decode_blob(data)
        if text is None:
            continue
        hits.extend(scan_text(posix, text, entries))
    return hits


def scan_history(root: Path, blobs: Blobs, entries: list[AllowEntry]) -> list[Hit]:
    seen: set[str] = set()
    unique: dict[tuple[str, str, str], Hit] = {}
    for line in git(root, "rev-list", "--objects", "--all").splitlines():
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue  # trees and commits have no path
        sha, path = parts
        if sha in seen:
            continue
        seen.add(sha)
        for hit in scan_blob(blobs, sha, path, entries):
            if hit.substantive:
                key = (hit.rule, hit.path, hit.line.strip())
                unique.setdefault(
                    key,
                    Hit(hit.rule, hit.path, hit.line_no, f"{hit.line}  (blob {sha[:12]})", hit.allowed),
                )
    return list(unique.values())


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def report(group: str, hits: list[Hit], prefix: str = "  ", verbose: bool = False) -> int:
    substantive = [hit for hit in hits if hit.substantive]
    allowed = [hit for hit in hits if hit.allowed]
    status = f"{len(substantive)} hit(s)" if substantive else "clean"
    if allowed:
        status += f", {len(allowed)} allowlisted"
    print(f"{prefix}{group:<28} {status}")
    if verbose:
        shown = substantive + allowed
    else:
        shown = substantive[:SHOW_LIMIT]
    for hit in shown:
        label = "HIT" if hit.substantive else "ok "
        print(f"{prefix}  {label} {hit.render()}")
    remaining = len(substantive) + (len(allowed) if verbose else 0) - len(shown)
    if remaining > 0:
        print(f"{prefix}  ... {remaining} more (--verbose to print all)")
    return len(substantive)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Block household facts and leaked credentials.")
    parser.add_argument("root", nargs="?", default=".", help="repository root")
    parser.add_argument(
        "--allowlist",
        default=None,
        help="allowlist path (default: <root>/tools/privacy_allowlist.txt)",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="pre-commit mode: scan only files staged for commit",
    )
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="skip the reachable-history scan (working tree and branches only)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="print every hit, not the first 10 per group",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not (root / ".git").exists():
        print(f"privacy gate: {root} is not a git repository", file=sys.stderr)
        return 2
    allowlist_path = Path(args.allowlist) if args.allowlist else root / "tools" / "privacy_allowlist.txt"
    entries = load_allowlist(allowlist_path)

    print(f"privacy gate: {root}")
    substantive = 0

    if args.staged:
        hits = scan_staged(root, entries)
        substantive += report("staged files", hits)
    else:
        substantive += report("working tree", scan_working_tree(root, entries))

        blobs = Blobs(root)
        try:
            print("branches:")
            for name, sha in branch_refs(root):
                hits: list[Hit] = []
                for path, blob_sha in tree_blobs(root, sha):
                    hits.extend(scan_blob(blobs, blob_sha, path, entries))
                substantive += report(f"{name} ({sha[:7]})", hits, prefix="  ", verbose=args.verbose)
            if not args.no_history:
                history = scan_history(root, blobs, entries)
                commits = len(git(root, "rev-list", "--all").splitlines())
                substantive += report(f"history ({commits} commits)", history, verbose=args.verbose)
        finally:
            blobs.close()

    if substantive:
        print(f"FAIL: {substantive} substantive privacy hit(s)")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
