#!/usr/bin/env python3
"""One-time migration of the site's v1 YAML data (src/data/*.yml) into the
knowledge graph sources under kg/.

Run from the repository root:

    python3 scripts/kg/migrate_v1.py

The script is kept in the repository as a record of how each v1 field maps
to the graph. It is deterministic: running it again over the same inputs
produces the same files. Since src/data/ has been removed, it reads the v1
files from git history (V1_REF below). Once kg/ is the source of truth, edit kg/ directly
and do not re-run this script.

What it does, field by field, is described in kg/README.md.
"""

from __future__ import annotations

import re
import struct
import subprocess
import sys
import unicodedata
from collections import Counter, OrderedDict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "data"
OUT = ROOT / "kg"
PUBLIC = ROOT / "public"

# Paths the data has lived at over the repository's history, oldest first.
HISTORY_PATHS = ["_data", "docs/_data", "src/data"]

# Last commit on main with the v1 data files. When src/data/ is gone, the
# inputs are read from this commit.
V1_REF = "67f490956e6461c5920169a080551683dd27452a"

LAB = "sid:org/sensein"
MCGOVERN = "sid:org/mcgovern-institute"
MIT = "sid:org/mit"
NIH = "sid:org/nih"

# NIH institute and center codes as they appear in award numbers.
NIH_IC = {
    "DA": ("sid:org/nida", "National Institute on Drug Abuse", "NIDA"),
    "MH": ("sid:org/nimh", "National Institute of Mental Health", "NIMH"),
    "NS": ("sid:org/ninds", "National Institute of Neurological Disorders and Stroke", "NINDS"),
    "EB": ("sid:org/nibib", "National Institute of Biomedical Imaging and Bioengineering", "NIBIB"),
    "OD": ("sid:org/nih-od", "NIH Office of the Director", "NIH OD"),
}

ACCOUNT_URL = {
    "github": "https://github.com/{}",
    "x": "https://x.com/{}",
    "bluesky": "https://bsky.app/profile/{}",
}


# ─── helpers ────────────────────────────────────────────────────────────────


def load_text(name: str) -> str:
    path = SRC / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return subprocess.run(["git", "show", f"{V1_REF}:src/data/{name}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


def load(name: str):
    data = yaml.safe_load(load_text(name))
    return data if data is not None else []


TODO = re.compile(r"#\s*TODO\b[:\s]*(.*)$")


def todo_markers(name: str, key: str = "slug") -> dict[str, list[str]]:
    """TODO markers left in a v1 file, by entry. YAML drops comments, and a
    marker inside a folded scalar ends up in the text itself, so both are
    recovered from the raw file and become curation notes."""
    out: dict[str, list[str]] = {}
    current = None
    for line in load_text(name).splitlines():
        m = re.match(rf"^-\s+{key}:\s*(\S+)", line)
        if m:
            current = m.group(1).strip("'\"")
        t = TODO.search(line)
        if t and current:
            field = re.match(r"^\s*-?\s*([a-z_]+):", line)
            note = t.group(1).strip() or (f"fill in {field.group(1)}" if field else "follow up")
            out.setdefault(current, []).append(note)
    return out


def strip_todo(text):
    if isinstance(text, str):
        return TODO.sub("", text).rstrip()
    return text


def slugify(text: str) -> str:
    """Same algorithm as personSlug() in src/lib/data.ts, so anchors on
    /team/ do not change."""
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(ch for ch in t if not ("̀" <= ch <= "ͯ"))
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


def clean(text):
    """Trim the trailing newlines that YAML folded scalars leave behind."""
    if isinstance(text, str):
        return text.strip()
    return text


_first_seen_cache: dict[str, str | None] = {}


def first_seen(needle: str) -> str | None:
    """Date (YYYY-MM-DD) of the first commit that added `needle` to the
    site's data files, or None if git history is not available. Dates are
    bounded below by the repository's first commit (2019-01-27)."""
    if needle in _first_seen_cache:
        return _first_seen_cache[needle]
    try:
        out = subprocess.run(
            ["git", "log", "--reverse", "--format=%cs", "-S", needle, "--", *HISTORY_PATHS],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.split()
        value = out[0] if out else None
    except (subprocess.CalledProcessError, FileNotFoundError):
        value = None
    _first_seen_cache[needle] = value
    return value


YEAR = re.compile(r"\b(?:19|20)\d{2}\b")


def years_span(text: str | None) -> tuple[str | None, str | None, bool]:
    """Parse the first and last year out of free text such as
    "2020 - 2025", "Fall 2020" or "2024–present".
    Returns (start, end, open_ended)."""
    if not text:
        return None, None, False
    found = YEAR.findall(str(text))
    if not found:
        return None, None, False
    open_ended = bool(re.search(r"present", str(text), re.I)) and len(found) == 1
    # "2012 - 209": a range whose end is not a readable year.
    broken_range = len(found) == 1 and re.search(r"\d\s*[–-]\s*\d", str(text))
    start = found[0]
    end = None if (open_ended or broken_range) else found[-1]
    return start, end, open_ended


def image_size(path: Path) -> tuple[int, int] | None:
    """Width and height of a WebP, PNG or JPEG file, read from its header."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        chunk = data[12:16]
        if chunk == b"VP8 ":
            w, h = struct.unpack("<HH", data[26:30])
            return w & 0x3FFF, h & 0x3FFF
        if chunk == b"VP8L":
            b = data[21:25]
            w = 1 + (((b[1] & 0x3F) << 8) | b[0])
            h = 1 + (((b[3] & 0x0F) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
            return w, h
        if chunk == b"VP8X":
            w = 1 + int.from_bytes(data[24:27], "little")
            h = 1 + int.from_bytes(data[27:30], "little")
            return w, h
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            length = struct.unpack(">H", data[i + 2:i + 4])[0]
            i += 2 + length
    return None


MEDIA = {".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg",
         ".jpeg": "image/jpeg", ".gif": "image/gif", ".svg": "image/svg+xml"}


class Graph:
    """Accumulates nodes by collection, keeping first-insertion order."""

    def __init__(self):
        self.c: dict[str, OrderedDict] = {}

    def add(self, collection: str, node: dict) -> dict:
        bucket = self.c.setdefault(collection, OrderedDict())
        nid = node["id"]
        if nid in bucket:
            return bucket[nid]
        bucket[nid] = node
        return node

    def get(self, collection: str, nid: str):
        return self.c.get(collection, {}).get(nid)


G = Graph()


def org(nid: str, name: str, **extra) -> str:
    node = {"id": nid, "name": name}
    node.update({k: v for k, v in extra.items() if v})
    G.add("organizations", node)
    return nid


def image(path: str | None, kind: str, depicts: list[str], caption: str | None = None) -> str | None:
    if not path:
        return None
    rel = path.lstrip("/")
    stem = re.sub(r"^images/", "", rel)
    stem = re.sub(r"\.[A-Za-z0-9]+$", "", stem)
    nid = "sid:image/" + "/".join(slugify(seg) for seg in stem.split("/"))
    existing = G.get("images", nid)
    if existing:
        for d in depicts:
            if d not in existing["depicts"]:
                existing["depicts"].append(d)
        return nid
    node = {"id": nid, "content_url": path, "image_kind": kind}
    if caption:
        node["caption"] = caption
    ext = Path(rel).suffix.lower()
    if ext in MEDIA:
        node["encoding_format"] = MEDIA[ext]
    size = image_size(PUBLIC / rel)
    if size:
        node["width"], node["height"] = size
    elif not (PUBLIC / rel).exists():
        node["curation_notes"] = [f"File not found under public/ at migration time: {path}"]
    node["depicts"] = list(depicts)
    node["derived_from"] = ["site-yaml-v1"]
    G.add("images", node)
    return nid


# ─── organizations ──────────────────────────────────────────────────────────


def build_core_orgs():
    org(MIT, "Massachusetts Institute of Technology", alternate_names=["MIT"],
        organization_type="university", url="https://www.mit.edu/")
    org(MCGOVERN, "McGovern Institute for Brain Research", alternate_names=["McGovern Institute"],
        organization_type="institute", parent_organization=MIT, url="https://mcgovern.mit.edu/")
    org(LAB, "Senseable Intelligence Group", alternate_names=["sensein"],
        organization_type="research_group", parent_organization=MCGOVERN,
        url="https://sensein.group/")
    org(NIH, "National Institutes of Health", alternate_names=["NIH"],
        organization_type="funder", url="https://www.nih.gov/")
    for nid, name, abbr in NIH_IC.values():
        org(nid, name, alternate_names=[abbr], organization_type="funder", parent_organization=NIH)


# ─── people and memberships ─────────────────────────────────────────────────


def role_category(info: str, roster: str) -> str:
    t = info or ""
    rules = [
        (r"\bDirector\b|Principal Investigator", "principal_investigator"),
        (r"\bVisiting\b|\bVisitor\b", "visitor"),
        (r"Post-?doc", "postdoc"),
        (r"Undergrad|UROP", "undergraduate"),
        (r"PhD|MD-PhD|MEng|MSc|M\.S\.|Master|Graduate|\bstudent\b", "graduate_student"),
        (r"Engineer", "engineer"),
        (r"Research Scientist|Senior Scientist|Scientist", "research_scientist"),
        (r"Technical (Associate|Assistant)|Intern|Contractor|Research Assistant|Research Specialist", "technical_staff"),
        (r"Administrative|Administrator", "administrative_staff"),
        (r"Affiliate", "affiliate"),
    ]
    for pattern, cat in rules:
        if re.search(pattern, t, re.I):
            return cat
    return "other"


CV_LINK = re.compile(r'^<a href="([^"]+)">\s*Full CV\s*</a>$', re.I)


def accounts_for(m: dict) -> list[dict]:
    out = []
    if m.get("github"):
        h = str(m["github"]).strip()
        out.append({"service": "github", "account_name": h, "url": ACCOUNT_URL["github"].format(h)})
    if m.get("linkedin"):
        u = str(m["linkedin"]).strip()
        name = re.search(r"/in/([^/?#]+)", u)
        acc = {"service": "linkedin", "url": u}
        if name:
            acc["account_name"] = name.group(1)
        out.append(acc)
    if m.get("scholar"):
        u = str(m["scholar"]).strip()
        user = re.search(r"[?&]user=([^&#]+)", u)
        acc = {"service": "google_scholar", "url": u}
        if user:
            acc["account_name"] = user.group(1)
        out.append(acc)
    if m.get("twitter"):
        h = str(m["twitter"]).strip().lstrip("@")
        out.append({"service": "x", "account_name": h, "url": ACCOUNT_URL["x"].format(h)})
    if m.get("bluesky"):
        h = str(m["bluesky"]).strip().lstrip("@")
        out.append({"service": "bluesky", "account_name": h, "url": ACCOUNT_URL["bluesky"].format(h)})
    return out


def person_from_roster(m: dict) -> str:
    name = m["name"].strip()
    slug = slugify(name)
    pid = f"sid:person/{slug}"
    node = {"id": pid, "name": name, "slug": slug}
    if m.get("website"):
        node["url"] = str(m["website"]).strip()
    if m.get("orcid"):
        node["orcid"] = "ORCID:" + str(m["orcid"]).strip()
    if m.get("email"):
        node["email"] = str(m["email"]).strip()
    img = image(m.get("photo"), "portrait", [pid])
    if img:
        node["image"] = img
    accounts = accounts_for(m)
    if accounts:
        node["accounts"] = accounts
    edu = []
    for i in range(1, 6):
        v = clean(m.get(f"education{i}"))
        if not v:
            continue
        cv = CV_LINK.match(v)
        if cv:
            node["cv"] = cv.group(1)
            continue
        edu.append({"statement": v})
    if edu:
        node["education"] = edu
    created = first_seen(name)
    if created:
        node["created"] = created
    node["derived_from"] = ["site-yaml-v1"]
    G.add("people", node)
    return pid


def build_people():
    rosters = [
        ("team_members.yml", "current", "members"),
        ("students.yml", "current", "students"),
        ("alumni_members.yml", "former", None),
    ]
    for fname, status, section in rosters:
        for order, m in enumerate(load(fname)):
            pid = person_from_roster(m)
            slug = pid.split("/", 1)[1]
            info = clean(m.get("info")) or ""
            ms = {
                "id": f"sid:membership/{slug}",
                "member": pid,
                "organization": LAB,
                "membership_status": status,
            }
            if info:
                ms["role_title"] = info
            ms["role_category"] = role_category(info, fname)
            if status == "current":
                started = re.search(r"started\s+((?:19|20)\d{2})", info, re.I)
                if started:
                    ms["start_date"] = started.group(1)
                ms["roster_section"] = section
            else:
                duration = clean(m.get("duration"))
                if duration:
                    ms["period_text"] = str(duration)
                    start, end, _ = years_span(duration)
                    if start:
                        ms["start_date"] = start
                    if end:
                        ms["end_date"] = end
            ms["roster_order"] = order + 1
            created = first_seen(m["name"].strip())
            if created:
                ms["created"] = created
            ms["derived_from"] = ["site-yaml-v1"]
            G.add("memberships", ms)


def person_stub(name: str, note: str | None = None) -> str:
    """A person who appears in the data without a roster entry."""
    name = name.strip()
    slug = slugify(name)
    pid = f"sid:person/{slug}"
    if not G.get("people", pid):
        node = {"id": pid, "name": name, "slug": slug, "derived_from": ["site-yaml-v1"]}
        if note:
            node["curation_notes"] = [note]
        G.add("people", node)
    return pid


# ─── topics and pages ───────────────────────────────────────────────────────

SCHEME = "sid:topics/research-areas"


def build_topics():
    page = load("publications_page.yml")
    G.add("topic_schemes", {
        "id": SCHEME,
        "title": "Research areas",
        "description": "Topic areas used to group the lab's projects and publications.",
        "derived_from": ["site-yaml-v1"],
    })
    featured = []
    for t in page.get("topics", []):
        tid = f"sid:topic/{t['tag']}"
        node = {"id": tid, "pref_label": t["label"], "notation": t["tag"], "in_scheme": SCHEME}
        if t.get("description"):
            node["definition"] = clean(t["description"])
        node["derived_from"] = ["site-yaml-v1"]
        G.add("topics", node)
        featured.append(tid)
    G.add("pages", {
        "id": "sid:page/publications",
        "path": "/publications/",
        "title": "Publications",
        "summary": clean(page.get("summary")),
        "keywords": list(page.get("keywords") or []),
        "featured_topics": featured,
        "derived_from": ["site-yaml-v1"],
    })


def topic_ref(tag: str) -> str:
    tid = f"sid:topic/{tag}"
    if not G.get("topics", tid):
        label = tag.replace("-", " ").capitalize()
        G.add("topics", {
            "id": tid, "pref_label": label, "notation": tag, "in_scheme": SCHEME,
            "derived_from": ["site-yaml-v1"],
            "curation_notes": [
                "Tag used on publications but missing from the topic list on "
                "/publications/; label written during migration, please review."
            ],
        })
    return tid


# ─── publications ───────────────────────────────────────────────────────────


def pub_iri(p: dict) -> str:
    if p.get("doi"):
        return "doi:" + p["doi"].strip().lower()
    if p.get("arxiv"):
        return "arxiv:" + p["arxiv"].strip()
    if p.get("pmid"):
        return "pmid:" + str(p["pmid"]).strip()
    return "sid:publication/" + slugify(p["id"])


def _fold(s: str) -> str:
    t = unicodedata.normalize("NFKD", s.lower())
    return "".join(ch for ch in t if not ("̀" <= ch <= "ͯ"))


def author_key(byline: str) -> tuple[str, str] | None:
    """(surname, first initial) of a byline name such as "Ghosh SS" or
    "Satrajit S. Ghosh"."""
    b = byline.strip().rstrip(".")
    if "," in b:
        surname, _, given = b.partition(",")
        given = given.strip()
        if surname.strip() and given:
            return _fold(surname.split()[-1]), _fold(given)[0]
    m = re.match(r"^(.+?)\s+([A-Z][A-Z\-]{0,4})$", b)
    if m:
        surname, initials = m.group(1), m.group(2)
        return _fold(surname.split()[-1]), initials[0].lower()
    parts = b.replace(",", " ").split()
    if len(parts) < 2:
        return None
    return _fold(parts[-1]), _fold(parts[0])[0]


def person_key(name: str) -> tuple[str, str]:
    parts = name.replace(",", " ").split()
    return _fold(parts[-1]), _fold(parts[0])[0]


PUB_INDEX: dict[str, str] = {}


def index_pub(p: dict, iri: str):
    for key in [p["id"], p.get("doi")]:
        if key:
            PUB_INDEX[str(key).strip().lower()] = iri
    if p.get("arxiv"):
        a = p["arxiv"].strip().lower()
        PUB_INDEX[f"arxiv:{a}"] = iri
        PUB_INDEX[f"10.48550/arxiv.{a}"] = iri
    if p.get("pmid"):
        PUB_INDEX[f"pmid:{p['pmid']}"] = iri


def build_publications(unmatched_authors: Counter):
    pubs = load("publications.yml")
    for p in pubs:
        iri = pub_iri(p)
        index_pub(p, iri)
        node = {
            "id": iri,
            "slug": p["id"],
            "publication_type": p["type"],
            "category": p["category"],
            "year": p["year"],
            "title": clean(p["title"]),
        }
        lab_ids = [person_stub(n) for n in p.get("lab_authors") or []]
        keys: dict[tuple[str, str], list[str]] = {}
        for n, pid in zip(p.get("lab_authors") or [], lab_ids):
            keys.setdefault(person_key(n), []).append(pid)
        matched = set()
        auths = []
        for i, a in enumerate(p.get("authors") or [], start=1):
            entry = {"position": i, "author_name": a}
            k = author_key(a)
            cands = keys.get(k, []) if k else []
            if len(cands) == 1 and cands[0] not in matched:
                entry["agent"] = cands[0]
                matched.add(cands[0])
            auths.append(entry)
        for pid in lab_ids:
            if pid not in matched:
                unmatched_authors[pid] += 1
        node["authorships"] = auths
        for k in ["venue", "doi", "pmid", "pmcid", "arxiv", "url", "pdf_url"]:
            if p.get(k):
                node[k] = str(p[k]).strip()
        if p.get("github"):
            g = str(p["github"]).strip()
            node["code_repository"] = g if g.startswith("http") else f"https://github.com/{g}"
        if p.get("projects"):
            node["projects"] = [f"sid:project/{s}" for s in p["projects"]]
        if lab_ids:
            node["lab_authors"] = lab_ids
        node["topics"] = [topic_ref(t) for t in p.get("topics") or []]
        if p.get("preprints"):
            pre = []
            for q in p["preprints"]:
                e = {"identifier": q["id"]}
                for k in ["venue", "url", "year", "doi", "arxiv"]:
                    if q.get(k):
                        e[k] = q[k]
                pre.append(e)
            node["preprints"] = pre
        if p.get("cited_by") is not None:
            node["cited_by_count"] = p["cited_by"]
        if p.get("abstract"):
            node["abstract"] = clean(p["abstract"])
        if p.get("abstract_source"):
            node["abstract_source"] = p["abstract_source"]
        if p.get("key_findings"):
            node["key_findings"] = clean(p["key_findings"])
        created = first_seen(p["id"])
        if created:
            node["created"] = created
        node["derived_from"] = list(p.get("sources") or []) + ["site-yaml-v1"]
        G.add("publications", node)


def find_pub(ref: str) -> str | None:
    return PUB_INDEX.get(ref.strip().lower())


def build_highlights():
    """The curated highlights in publist.yml become a Highlight on the
    matching Publication, with the figure as an Image node."""
    for rank, h in enumerate(load("publist.yml"), start=1):
        url = (h.get("link") or {}).get("url", "")
        iri = None
        m = re.search(r"doi\.org/(.+)$", url)
        if m:
            iri = find_pub(m.group(1))
        if not iri:
            t = _fold(clean(h["title"]))
            for node in G.c["publications"].values():
                if _fold(node["title"]).startswith(t):
                    iri = node["id"]
                    break
        if not iri:
            print(f"warning: highlight not matched to a publication: {h['title']}", file=sys.stderr)
            continue
        pub = G.get("publications", iri)
        hl = {"rank": rank}
        if h.get("description"):
            hl["summary"] = clean(h["description"])
        disp = (h.get("link") or {}).get("display")
        if disp:
            hl["citation_text"] = clean(disp)
        notes = [clean(h[k]) for k in ("news1", "news2") if h.get(k)]
        code = h.get("code link") or {}
        if code.get("url"):
            label = code.get("display") or "Code"
            notes.append(f'<a href="{code["url"]}">{label}</a>')
        if notes:
            hl["notes"] = notes
        pub["highlight"] = hl
        if url and not pub.get("url"):
            pub["url"] = url
        fig = image(h.get("image"), "figure", [iri])
        if fig:
            pub.setdefault("figures", []).append(fig)


# ─── projects and grants ────────────────────────────────────────────────────

AWARD = re.compile(r"\b([A-Z]\d{2}|[A-Z]{2}\d)\s+([A-Z]{2})(\d{6})\b")
ROLE = re.compile(r"^(Lead PI|Site PI|Site Co-I|Co-PI|Co-I|MPI|PI)\b[;,]?\s*(.*)$")


def build_grants_from(statement: str | None) -> list[str]:
    if not statement:
        return []
    ids = []
    for m in AWARD.finditer(statement):
        activity, ic, serial = m.groups()
        if ic not in NIH_IC:
            continue
        gid = f"sid:grant/{activity.lower()}-{ic.lower()}{serial}"
        ids.append(gid)
        if G.get("grants", gid):
            continue
        node = {"id": gid, "award_number": f"{activity} {ic}{serial}", "funder": NIH_IC[ic][0]}
        # The parenthetical right after the award number, if any.
        tail = statement[m.end():]
        paren = re.match(r"\s*\(([^)]*)\)", tail)
        if paren:
            inner = paren.group(1).strip()
            first, _, rest = inner.partition(";")
            rm = ROLE.match(first.strip())
            if rm:
                node["lab_role"] = rm.group(1)
                leftover = ", ".join(x for x in [rm.group(2).strip(" ,"), rest.strip()] if x)
            else:
                leftover = inner
            span = re.search(r"\b((?:19|20)\d{2})\s*[–-]\s*((?:19|20)\d{2})\b", inner)
            if span:
                node["start_date"], node["end_date"] = span.group(1), span.group(2)
                leftover = re.sub(r",?\s*\b(?:19|20)\d{2}\s*[–-]\s*(?:19|20)\d{2}\b", "", leftover).strip(" ,;")
            if leftover:
                node["note"] = leftover
        node["derived_from"] = ["site-yaml-v1"]
        G.add("grants", node)
    return ids


def build_projects(roster_names: set[str]):
    todos = todo_markers("projects.yml")
    for p in load("projects.yml"):
        slug = p["slug"]
        pid = f"sid:project/{slug}"
        node = {
            "id": pid,
            "slug": slug,
            "title": strip_todo(clean(p["title"])),
            "project_type": "lab_project",
            "project_status": p["status"],
        }
        if p.get("description"):
            node["description"] = strip_todo(clean(p["description"]))
        if p.get("funder"):
            node["funding_statement"] = clean(p["funder"])
            grants = build_grants_from(p["funder"])
            if grants:
                node["funded_by"] = list(dict.fromkeys(grants))
        img = image(p.get("image"), "logo" if "logo" in (p.get("image") or "") else "project_image", [pid])
        if img:
            node["image"] = img
        if p.get("themes"):
            node["themes"] = [topic_ref(t) for t in p["themes"]]
        links = []
        for ln in p.get("links") or []:
            if ln.get("url"):
                # Site-relative links ("/riverst/") stay relative; the JSON-LD
                # context sets @base to the site, so in RDF they resolve to
                # https://sensein.group/riverst/.
                e = {"url": ln["url"]}
                if ln.get("label"):
                    e["label"] = ln["label"]
                links.append(e)
        if links:
            node["links"] = links
        contrib = p.get("contributors") or {}
        cur = [person_stub(n) for n in contrib.get("current") or []]
        former = []
        for n in contrib.get("former") or []:
            note = None if n.strip() in roster_names else (
                "Named as a former contributor to a lab project but not on the lab roster.")
            former.append(person_stub(n, note))
        if cur:
            node["members"] = cur
        if former:
            node["former_members"] = former
        if contrib.get("external"):
            node["external_contributors"] = [clean(x) for x in contrib["external"]]
        anchors, missing = [], []
        for ref in p.get("publications") or []:
            iri = find_pub(ref)
            (anchors if iri else missing).append(iri or ref)
        if anchors:
            node["anchor_publications"] = list(dict.fromkeys(anchors))
        notes = [f"Anchor publication not in the corpus: {r}" for r in missing]
        notes += [f"To do (from the old site data): {t}" for t in todos.get(slug, [])]
        if notes:
            node["curation_notes"] = notes
        created = first_seen(f"slug: {slug}")
        if created:
            node["created"] = created
        node["derived_from"] = ["site-yaml-v1"]
        G.add("projects", node)


def community_effort(name: str) -> str:
    slug = slugify(name)
    pid = f"sid:project/{slug}"
    if not G.get("projects", pid):
        G.add("projects", {
            "id": pid, "slug": slug, "title": name, "project_type": "community_effort",
            "derived_from": ["site-yaml-v1"],
        })
    return pid


def build_collaborations():
    lab_slugs = {n["slug"] for n in G.c["projects"].values()}
    for c in load("collaborators.yml"):
        note_inst = c.get("current_institution")
        pid = person_stub(c["name"])
        person = G.get("people", pid)
        if note_inst:
            oid = org(f"sid:org/{slugify(note_inst)}", clean(note_inst))
            person.setdefault("affiliations", [])
            if oid not in person["affiliations"]:
                person["affiliations"].append(oid)
        created = first_seen(c["name"].strip())
        if created and "created" not in person:
            person["created"] = created
        projs = []
        for x in c.get("projects") or []:
            projs.append(f"sid:project/{x}" if x in lab_slugs else community_effort(x))
        node = {"id": f"sid:collaboration/{pid.split('/', 1)[1]}", "collaborator": pid}
        if projs:
            node["projects"] = projs
        years = c.get("years")
        if years:
            node["period_text"] = str(years)
            start, end, _ = years_span(years)
            if start:
                node["start_date"] = start
            if end:
                node["end_date"] = end
        if c.get("note"):
            node["note"] = clean(c["note"])
        if created:
            node["created"] = created
        node["derived_from"] = ["site-yaml-v1"]
        G.add("collaborations", node)


# ─── news ───────────────────────────────────────────────────────────────────


def build_news():
    seen = Counter()
    for n in load("news.yml"):
        raw = str(n["date"]).strip()
        parts = re.match(r"^(\d{4})\s+(\d{1,2})\s+(\d{1,2})", raw)
        if parts:
            y, mth, d = parts.groups()
            date = f"{y}-{int(mth):02d}-{int(d):02d}"
        else:
            date = raw[:4]
        seen[date] += 1
        nid = f"sid:news/{date}" + (f"-{seen[date]}" if seen[date] > 1 else "")
        node = {"id": nid, "date_published": date, "headline": clean(n["headline"])}
        if raw != f"{date[:4]} {date[5:7]} {date[8:10]}":
            node["period_text"] = raw
        node["derived_from"] = ["site-yaml-v1"]
        G.add("news", node)


# ─── output ─────────────────────────────────────────────────────────────────

FILES = [
    ("organizations", "organizations.yaml", "Organizations: the lab, its host institutions, funders and collaborators' institutions."),
    ("people", "people.yaml", "People: current and past lab members, and external collaborators. Roles in the lab are in memberships.yaml."),
    ("memberships", "memberships.yaml", "Time-bounded roles of people in the lab. A person with no end_date is a current member."),
    ("collaborations", "collaborations.yaml", "Working relationships between the lab and external people."),
    ("projects", "projects.yaml", "Research projects (lab_project) and community efforts the lab contributes to (community_effort)."),
    ("grants", "grants.yaml", "Funding awards, linked from projects through funded_by."),
    ("publications", "publications.yaml", "The publications corpus. Ordered bylines are in authorships; featured papers carry a highlight."),
    ("images", "images.yaml", "Image files the site serves: portraits, project images, figures and logos."),
    ("topic_schemes", "topics.yaml", None),
    ("topics", "topics.yaml", "Research areas used to group projects and publications."),
    ("news", "news.yaml", "Dated announcements."),
    ("pages", "pages.yaml", "Editable text for pages whose layout lives in the site code."),
]


class Dumper(yaml.SafeDumper):
    pass


def _str(dumper, data):
    if "\n" in data or len(data) > 100:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=">" if "\n" not in data else "|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


Dumper.add_representer(str, _str)
Dumper.add_representer(OrderedDict, lambda d, data: d.represent_dict(data.items()))


def write_files():
    OUT.mkdir(exist_ok=True)
    grouped: dict[str, list] = OrderedDict()
    for coll, fname, desc in FILES:
        grouped.setdefault(fname, []).append((coll, desc))
    for fname, parts in grouped.items():
        doc = OrderedDict()
        header = [d for _, d in parts if d]
        for coll, _ in parts:
            nodes = list(G.c.get(coll, {}).values())
            if nodes:
                doc[coll] = nodes
        text = yaml.dump(doc, Dumper=Dumper, sort_keys=False, allow_unicode=True, width=100)
        banner = "# " + "\n# ".join(header) + "\n# Schema: schema/sensein.yaml. Build: python3 scripts/kg/build.py\n\n"
        (OUT / fname).write_text(banner + text, encoding="utf-8")


def main():
    build_core_orgs()
    build_people()
    roster_names = {n["name"] for n in G.c["people"].values()}
    build_topics()
    unmatched = Counter()
    build_publications(unmatched)
    build_highlights()
    build_projects(roster_names)
    build_collaborations()
    build_news()
    write_files()
    counts = {k: len(v) for k, v in G.c.items()}
    print("wrote kg/:", counts)
    if unmatched:
        print("lab authors not matched to a byline position:", sum(unmatched.values()), file=sys.stderr)


if __name__ == "__main__":
    main()
