#!/usr/bin/env python3
"""Folio — the resume workbench: lint, evidence ledger, keyword gap, docx render.

Input is one markdown file in the canonical shape (see
`bots/resume/skills/resume-rewrite/SKILL.md`):

    # Name
    CITY, ST · email · phone

    ## Professional Summary
    ...
    ## Core Skills
    - ...
    ## Experience

    ### Title — Employer, City, ST
    *2019 – 2022*
    - bullet

Everything here is deterministic and offline. It never invents a fact: a bullet
with no number is reported, not filled in.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

FIRST_PERSON = re.compile(r"(?<![\w'])(I|I'm|I've|my|My|me|we|We|our|Our)(?![\w'])")
STREET = re.compile(
    r"\b(?:\d{1,6}\s+)?(?:[A-Z][\w.'-]*\s+){0,3}"
    r"(?:Rd|Road|St|Street|Ave|Avenue|Ln|Lane|Dr|Drive|Blvd|Boulevard|Ct|Court|Pkwy|Cir)\b",
)
CLICHES = (
    "hard worker",
    "team player",
    "wear a smile",
    "passionate",
    "go-getter",
    "self-starter",
    "think outside the box",
    "detail-oriented",
    "works well under pressure",
    "people person",
    "seeking a challenging",
    "excited to join",
    "results-driven",
)
DUTY_OPENERS = (
    "responsible for",
    "duties included",
    "tasked with",
    "helped with",
    "worked with",
    "assisted with",
)
HOMEMAKER = re.compile(r"\b(stay[\s-]at[\s-]home\s+(mom|dad|parent)|homemaker)\b", re.I)
REFERENCES = re.compile(r"references?\s+(are\s+)?(available|upon request)", re.I)
MAX_BULLET = 240

YEAR = re.compile(r"(19|20)\d{2}")
DATE_RANGE = re.compile(
    r"(?:[A-Za-z]{3,9}\.?\s+)?(\d{4})\s*[–—-]+\s*"
    r"(Present|Current|Now|(?:[A-Za-z]{3,9}\.?\s+)?(\d{4}))"
)

# Vocabulary used by the keyword gap pass. Hospitality-weighted on purpose;
# extend per bot use, never per resume.
VOCAB = (
    "alcohol service", "banquet", "bar inventory", "bartending", "beer", "beverage",
    "cash handling", "catering", "cocktail", "compliance", "conflict resolution",
    "cost control", "customer service", "customer satisfaction", "food safety",
    "front of house", "guest experience", "hospitality", "inventory", "labor cost",
    "menu knowledge", "order accuracy", "plating", "POS", "prep", "private events",
    "quality assurance", "restaurant", "safety", "sanitation", "scheduling",
    "server", "shift lead", "staff training", "team leadership", "tips", "upselling",
    "wine", "banquet captain", "food handler", "servsafe", "TABC", "Toast", "Micros",
    "Aloha", "Square", "7shifts", "HotSchedules", "training program",
    "performance review", "open availability", "multi-unit", "ticket times",
)

STOPWORDS = {
    "and", "the", "for", "with", "you", "your", "our", "are", "will", "that", "this",
    "have", "has", "from", "not", "but", "all", "can", "who", "was", "were", "their",
    "they", "them", "its", "into", "out", "per", "own", "any", "may", "must", "able",
    "work", "working", "team", "teams", "ability", "including", "such", "other",
    "well", "more", "than", "when", "while", "each", "help", "ensure", "providing",
    "provide", "role", "job", "position", "company", "applicants", "candidate",
}


@dataclass
class Bullet:
    text: str
    line: int


@dataclass
class Role:
    title: str
    employer: str
    location: str
    dates: str
    start: int | None
    end: int | None
    current: bool
    bullets: list[Bullet] = field(default_factory=list)
    line: int = 0

    @property
    def company(self) -> str:
        return self.employer.strip()


@dataclass
class Resume:
    name: str
    contact: list[str]
    summary: str
    skills: list[str]
    roles: list[Role]
    sections: list[str]
    extras: list[str] = field(default_factory=list)

    def text(self) -> str:
        parts = [self.name, *self.contact, self.summary, *self.skills]
        for role in self.roles:
            parts += [role.title, role.employer, role.location, role.dates]
            parts += [b.text for b in role.bullets]
        parts += self.extras
        return "\n".join(parts)


def _split_dates(dates: str) -> tuple[int | None, int | None, bool]:
    match = DATE_RANGE.search(dates)
    if not match:
        years = [int(y) for y in YEAR.findall(dates.replace("–", "-"))]
        start = years[0] if years else None
        end = years[-1] if len(years) > 1 else None
        return start, end, False
    start = int(match.group(1))
    end = int(match.group(3)) if match.group(3) else None
    current = match.group(2).lower() in {"present", "current", "now"}
    return start, end, current


def parse(text: str) -> Resume:
    lines = text.splitlines()
    name = ""
    contact: list[str] = []
    summary_bits: list[str] = []
    skills: list[str] = []
    roles: list[Role] = []
    sections: list[str] = []
    extras: list[str] = []
    current_section = ""
    role: Role | None = None

    for index, raw in enumerate(lines, start=1):
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# ") and not name:
            name = stripped[2:].strip()
            continue
        if stripped.startswith("## "):
            current_section = stripped[3:].strip().lower()
            sections.append(stripped[3:].strip())
            role = None
            continue
        if stripped.startswith("### "):
            head = stripped[4:].strip()
            title, employer, location = head, "", ""
            if "—" in head or " - " in head:
                sep = "—" if "—" in head else " - "
                left, right = head.split(sep, 1)
                title = left.strip()
                employer, location = _split_employer(right)
            roles.append(Role(title, employer, location, "", None, None, False, line=index))
            role = roles[-1]
            continue
        if role is not None and stripped.startswith("*") and not stripped.startswith("* "):
            role.dates = stripped.strip("*").strip()
            role.start = None
            role.start, role.end, role.current = _split_dates(role.dates)
            continue
        if role is not None and stripped.startswith(("- ", "* ")):
            role.bullets.append(Bullet(stripped[2:].strip(), index))
            continue
        if not name:
            continue
        if not current_section:
            contact.append(stripped)
            continue
        if current_section.startswith(("professional summary", "summary", "objective")):
            summary_bits.append(stripped)
            continue
        if current_section.startswith("core skills") or current_section == "skills":
            if stripped.startswith(("- ", "* ")):
                skills.append(stripped[2:].strip())
            continue
        extras.append(stripped)
    return Resume(name, contact, " ".join(summary_bits), skills, roles, sections, extras)


def _split_employer(right: str) -> tuple[str, str]:
    """Split 'Employer, City, ST' into employer and location."""
    parts = [p.strip() for p in right.strip().split(",") if p.strip()]
    if len(parts) >= 3:
        return ", ".join(parts[:-2]), ", ".join(parts[-2:])
    if len(parts) == 2:
        if re.fullmatch(r"[A-Z]{2}(\s+\d{5})?", parts[1]):
            return parts[0], parts[1]
        return ", ".join(parts), ""
    return (parts[0] if parts else ""), ""


def _finding(level: str, code: str, where: str, message: str) -> dict:
    return {"level": level, "code": code, "where": where, "message": message}


def lint(resume: Resume) -> list[dict]:
    findings: list[dict] = []
    if not resume.name:
        findings.append(_finding("error", "no-name", "header", "No `# Name` line."))
    contact_blob = " ".join(resume.contact)
    if STREET.search(contact_blob):
        findings.append(
            _finding("error", "street-address", "contact",
                     "Full street address in the header. City, ST ZIP only — a street line is a privacy leak, not a credential.")
        )
    if not any("@" in c for c in resume.contact):
        findings.append(_finding("error", "no-email", "contact", "No email address in the header."))
    if not any(re.search(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", c) for c in resume.contact):
        findings.append(_finding("warn", "no-phone", "contact", "No phone number in the header."))

    if not resume.summary:
        findings.append(_finding("warn", "no-summary", "summary",
                                 "No professional summary; an objective paragraph is not a summary."))
    else:
        lowered_summary = resume.summary.lower()
        for cliche in CLICHES:
            if cliche in lowered_summary:
                findings.append(_finding("warn", "cliche", "summary",
                                         f"Cliche {cliche!r} in the summary; the summary earns its lines with "
                                         "years, certifications and scale, not adjectives."))
    if "objective" in {s.lower() for s in resume.sections}:
        findings.append(_finding("warn", "objective-heading", "summary",
                                 "\"Objective\" reads as what the applicant wants. Replace the heading with "
                                 "\"Professional Summary\" and lead with what the employer gets."))
    if not resume.skills:
        findings.append(_finding("warn", "no-skills", "skills",
                                 "No skills section — ATS keyword matching starts here."))

    if REFERENCES.search(resume.text()):
        findings.append(_finding("warn", "references-line", "footer",
                                 "\"References available upon request\" is obsolete; delete the line."))
    for match in HOMEMAKER.finditer(resume.text()):
        findings.append(_finding("warn", "homemaker-title", "experience",
                                 f"Career-break phrasing {match.group(0)!r}: reframe as the work performed "
                                 "(household and small-business administration), not the status."))

    seen: dict[str, int] = {}
    for role in resume.roles:
        if role.employer:
            key = role.employer.lower()
            seen[key] = seen.get(key, 0) + 1
    for employer, count in seen.items():
        if count > 1:
            findings.append(_finding("warn", "duplicate-employer", "experience",
                                     f"{employer!r} appears in {count} separate blocks; consolidate into one "
                                     "entry with progressive titles."))

    dated = [r for r in resume.roles if r.start]
    for prev, nxt in zip(dated, dated[1:]):
        prev_key = prev.end if prev.end else 9999
        nxt_key = nxt.end if nxt.end else 9999
        if nxt_key > prev_key:
            findings.append(_finding("error", "date-order", f"experience:{prev.employer}",
                                     f"{prev.employer or prev.title} ({prev.dates}) is listed before "
                                     f"{nxt.employer or nxt.title} ({nxt.dates}); experience must run newest first."))

    for role in resume.roles:
        where = f"{role.employer or role.title}"
        if not role.dates:
            findings.append(_finding("error", "no-dates", f"experience:{where}",
                                     "Role has no date line; an undated role reads as a gap."))
        if not role.bullets:
            findings.append(_finding("warn", "no-bullets", f"experience:{where}",
                                     "Role has no bullets — a title with no evidence is invisible."))
        if not role.location:
            findings.append(_finding("warn", "no-location", f"experience:{where}",
                                     "Role has no location; ATS locality matching uses it."))
        quantified = 0
        for bullet in role.bullets:
            text = bullet.text
            label = f"experience:{where}:{bullet.line}"
            if FIRST_PERSON.search(text):
                findings.append(_finding("error", "first-person", label,
                                         f"First person in bullet: {text[:60]!r} — drop the pronoun, start on a verb."))
            if re.search(r"\d", text):
                quantified += 1
            elif "[[CONFIRM" in text:
                findings.append(_finding("warn", "pending-confirm", label,
                                         f"Bullet awaits a fact the client must supply: {text[:70]!r}"))
            else:
                findings.append(_finding("warn", "no-metric", label,
                                         f"No number in bullet: {text[:60]!r} — add a count, a rate, or a size, "
                                         "or cut the bullet."))
            if len(text) > MAX_BULLET:
                findings.append(_finding("warn", "long-bullet", label,
                                         f"{len(text)} chars; a bullet over {MAX_BULLET} stops being scannable."))
            lowered = text.lower()
            for opener in DUTY_OPENERS:
                normalized = re.sub(r"^(i\s+(was|am|have)\s+)", "", lowered)
                if normalized.startswith(opener):
                    findings.append(_finding("error", "duty-opener", label,
                                             f"Starts with {opener!r} — name the verb and the result."))
                    break
            for cliche in CLICHES:
                if cliche in lowered:
                    findings.append(_finding("warn", "cliche", label, f"Cliche {cliche!r}; show the evidence instead."))
        if role.bullets and quantified == 0:
            findings.append(_finding("warn", "role-unquantified", f"experience:{where}",
                                     "No bullet in this role carries a number."))
    return findings


def ledger(resume: Resume) -> str:
    """Render the evidence ledger: one block per role, each bullet traceable."""
    out = [f"# Evidence ledger — {resume.name or '(unnamed)'}", ""]
    out.append("Every line below is either sourced from a resume page or marked `[[CONFIRM]]`.")
    out.append("A metric that was never measured stays a marker; it is never filled with a guess.")
    out.append("")
    if resume.summary:
        out += ["## Summary as written", "", resume.summary, ""]
    if resume.skills:
        out += ["## Skills as written", ""] + [f"- {s}" for s in resume.skills] + [""]
    out += ["## Roles", "", "| Role | Employer | Dates | Bullets | Quantified |", "|---|---|---|---|---|"]
    for role in resume.roles:
        q = sum(1 for b in role.bullets if re.search(r"\d", b.text))
        out.append(f"| {role.title} | {role.employer or '[[CONFIRM]]'} | {role.dates or '[[CONFIRM]]'} | "
                   f"{len(role.bullets)} | {q}/{len(role.bullets)} |")
    out.append("")
    for role in resume.roles:
        out += [f"### {role.title} — {role.employer or '[[CONFIRM: employer]]'}"
                f"{', ' + role.location if role.location else ''}",
                f"*{role.dates or '[[CONFIRM: dates]]'}*", ""]
        for bullet in role.bullets:
            marker = "" if re.search(r"\d", bullet.text) else "  `[[CONFIRM: metric]]`"
            out.append(f"- ({bullet.line}) {bullet.text}{marker}")
        out.append("")
    return "\n".join(out)


def keywords(resume_text: str, posting: str, limit: int = 25) -> dict:
    haystack = resume_text.lower()
    tokens = re.findall(r"[A-Za-z][A-Za-z+#/.'-]{1,}", posting)
    counts: dict[str, int] = {}
    for token in tokens:
        low = token.lower().strip(".'-")
        if low in STOPWORDS or len(low) < 3 or low.isdigit():
            continue
        counts[low] = counts.get(low, 0) + 1
    candidates = {k for k, v in counts.items() if v >= 2}
    candidates |= {term.lower() for term in VOCAB if term.lower() in posting.lower()}
    covered, missing = [], []
    for term in sorted(candidates):
        (covered if term in haystack else missing).append(term)
    missing.sort(key=lambda t: (-counts.get(t, 1), t))
    return {
        "covered": covered,
        "missing": missing[:limit],
        "coverage": round(len(covered) / max(1, len(candidates)), 2),
    }


def render_docx(resume: Resume, out_path: Path) -> Path:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt, Inches

    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.6)
        section.bottom_margin = Inches(0.6)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    head = doc.add_paragraph()
    head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = head.add_run(resume.name)
    run.bold = True
    run.font.size = Pt(19)

    contact = doc.add_paragraph(" · ".join(resume.contact))
    contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in contact.runs:
        r.font.size = Pt(10)

    def heading(text: str) -> None:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(text.upper())
        r.bold = True
        r.font.size = Pt(11)

    if resume.summary:
        heading("Professional Summary")
        doc.add_paragraph(resume.summary)
    if resume.skills:
        heading("Core Skills")
        doc.add_paragraph(" · ".join(resume.skills))
    if resume.roles:
        heading("Experience")
    for role in resume.roles:
        line = doc.add_paragraph()
        line.paragraph_format.space_before = Pt(7)
        line.paragraph_format.space_after = Pt(0)
        left = line.add_run(role.title)
        left.bold = True
        if role.employer:
            line.add_run(f" — {role.employer}" + (f", {role.location}" if role.location else ""))
        dates = doc.add_paragraph()
        dates.paragraph_format.space_after = Pt(2)
        dr = dates.add_run(role.dates)
        dr.italic = True
        dr.font.size = Pt(10)
        for bullet in role.bullets:
            p = doc.add_paragraph(bullet.text, style="List Bullet")
            p.paragraph_format.space_after = Pt(2)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="resume.py", description="Folio resume workbench")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_lint = sub.add_parser("lint", help="audit a resume markdown for ATS and quality failures")
    p_lint.add_argument("resume")
    p_lint.add_argument("--json", action="store_true")
    p_lint.add_argument("--strict", action="store_true", help="exit 1 on warnings too")

    p_led = sub.add_parser("ledger", help="render the evidence ledger from a resume")
    p_led.add_argument("resume")
    p_led.add_argument("-o", "--out")

    p_kw = sub.add_parser("keywords", help="compare resume text to a job posting")
    p_kw.add_argument("resume")
    p_kw.add_argument("posting")

    p_rd = sub.add_parser("render", help="render resume markdown to an ATS-safe .docx")
    p_rd.add_argument("resume")
    p_rd.add_argument("-o", "--out", required=True)

    args = parser.parse_args(argv)
    text = Path(args.resume).read_text(encoding="utf-8")
    resume = parse(text)

    if args.cmd == "lint":
        findings = lint(resume)
        errors = [f for f in findings if f["level"] == "error"]
        if args.json:
            print(json.dumps({"findings": findings, "errors": len(errors), "warnings": len(findings) - len(errors)}, indent=2))
        else:
            for f in findings:
                print(f"{f['level']:5} {f['code']:20} {f['where']:40} {f['message']}")
            print(f"\n{len(errors)} errors, {len(findings) - len(errors)} warnings, "
                  f"{len(resume.roles)} roles, {sum(len(r.bullets) for r in resume.roles)} bullets")
        return 1 if errors or (args.strict and findings) else 0
    if args.cmd == "ledger":
        body = ledger(resume)
        if args.out:
            Path(args.out).write_text(body, encoding="utf-8")
            print(f"wrote {args.out} ({len(resume.roles)} roles)")
        else:
            print(body)
        return 0
    if args.cmd == "keywords":
        posting = Path(args.posting).read_text(encoding="utf-8")
        report = keywords(resume.text(), posting)
        print(json.dumps(report, indent=2))
        return 0
    if args.cmd == "render":
        path = render_docx(resume, Path(args.out))
        print(f"wrote {path}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
