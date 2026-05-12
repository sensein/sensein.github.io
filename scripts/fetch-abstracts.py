#!/usr/bin/env python3
"""
Populate `abstract`, `abstract_source`, and (later, manually) `key_findings`
on every entry in publications.yml that has any of {pmid, pmcid, doi, arxiv}.

Sources (priority order, first hit wins):
    1. PubMed efetch (if pmid set)
    2. arXiv API (if arxiv set)
    3. OpenAlex DOI lookup (if doi set; needs abstract_inverted_index)
    4. Crossref DOI lookup (last resort, if doi set)

Rate-limits respected (NCBI ≤3/s, arXiv ~1/s, OpenAlex/Crossref ≤5/s).

The script ONLY fetches abstracts; `key_findings` is added in a later
manual pass driven by the agent.
"""

from __future__ import annotations

import html as html_mod
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path("/home/user/sensein.github.io")
DATA = ROOT / "src" / "data" / "publications.yml"

USER_AGENT = "sensein.github.io fetch-abstracts (mailto:satra@mit.edu)"
TIMEOUT = 30

# Entries whose authoritative sources only return non-abstract content
# (GitHub release notes, page header stubs, mismatched OpenAlex records).
# Recorded here so re-runs do not re-introduce false abstracts.
SKIP_IDS = {
    "10.21105/joss.05839",
    "10.3389/fnins.2013.00162",
    "10.1080/03008200500344017",
}

PUBMED_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
ARXIV_URL = "https://export.arxiv.org/api/query"
OPENALEX_URL = "https://api.openalex.org/works/doi:"
CROSSREF_URL = "https://api.crossref.org/works/"

# Last-call timestamps for per-source rate limiting.
_last: dict[str, float] = {}
MIN_INTERVAL = {
    "pubmed": 0.35,
    "arxiv": 1.05,
    "openalex": 0.20,
    "crossref": 0.20,
}


def throttle(key: str) -> None:
    now = time.monotonic()
    last = _last.get(key, 0.0)
    delta = now - last
    needed = MIN_INTERVAL[key] - delta
    if needed > 0:
        time.sleep(needed)
    _last[key] = time.monotonic()


def http_get(url: str, accept: str | None = None, retries: int = 2) -> tuple[int, bytes]:
    last_err = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        if accept:
            req.add_header("Accept", accept)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.getcode(), r.read()
        except urllib.error.HTTPError as e:
            # Don't retry hard client errors.
            if 400 <= e.code < 500 and e.code not in (408, 429):
                return e.code, b""
            last_err = e
        except Exception as e:
            last_err = e
        if attempt < retries:
            time.sleep(1.5 * (attempt + 1))
    sys.stderr.write(f"    HTTP error for {url}: {last_err}\n")
    return 0, b""


# ---------------------------------------------------------------- utilities

_WS = re.compile(r"\s+")
_TAGS = re.compile(r"<[^>]+>")


def clean_text(s: str) -> str:
    if not s:
        return ""
    s = html_mod.unescape(s)
    s = _TAGS.sub(" ", s)
    s = _WS.sub(" ", s).strip()
    return s


# -------------------------------------------------------------------- PubMed


def fetch_pubmed(pmid: str) -> str | None:
    throttle("pubmed")
    q = urllib.parse.urlencode(
        {"db": "pubmed", "id": pmid, "rettype": "abstract", "retmode": "xml"}
    )
    code, body = http_get(f"{PUBMED_URL}?{q}", accept="application/xml")
    if code != 200 or not body:
        return None
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return None
    # Find AbstractText nodes (possibly multiple labelled sections).
    nodes = root.findall(".//Abstract/AbstractText")
    if not nodes:
        return None
    parts: list[str] = []
    for n in nodes:
        # Inline tags (e.g., <i>, <sub>) -> stringify the element's full text.
        inner = "".join(n.itertext()) or ""
        inner = clean_text(inner)
        if not inner:
            continue
        label = n.attrib.get("Label")
        if label:
            parts.append(f"{label}: {inner}")
        else:
            parts.append(inner)
    if not parts:
        return None
    return clean_text(" ".join(parts))


# --------------------------------------------------------------------- arXiv

_ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}


def fetch_arxiv(arxiv_id: str) -> str | None:
    throttle("arxiv")
    q = urllib.parse.urlencode({"id_list": arxiv_id})
    code, body = http_get(f"{ARXIV_URL}?{q}")
    if code != 200 or not body:
        return None
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return None
    entry = root.find("a:entry", _ATOM_NS)
    if entry is None:
        return None
    summary = entry.find("a:summary", _ATOM_NS)
    if summary is None or not (summary.text or "").strip():
        return None
    return clean_text(summary.text)


# ------------------------------------------------------------------ OpenAlex


def fetch_openalex(doi: str) -> str | None:
    throttle("openalex")
    enc = urllib.parse.quote(doi, safe="")
    code, body = http_get(f"{OPENALEX_URL}{enc}")
    if code != 200 or not body:
        return None
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return None
    inv = data.get("abstract_inverted_index")
    if not inv:
        return None
    # Rebuild abstract: word -> [positions] -> sorted by position.
    pairs: list[tuple[int, str]] = []
    for word, positions in inv.items():
        for p in positions:
            pairs.append((p, word))
    if not pairs:
        return None
    pairs.sort(key=lambda kv: kv[0])
    text = " ".join(w for _, w in pairs)
    text = clean_text(text)
    return text or None


# ------------------------------------------------------------------ Crossref


def fetch_crossref(doi: str) -> str | None:
    throttle("crossref")
    enc = urllib.parse.quote(doi, safe="")
    code, body = http_get(f"{CROSSREF_URL}{enc}")
    if code != 200 or not body:
        return None
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return None
    msg = data.get("message", {})
    abs_html = msg.get("abstract")
    if not abs_html:
        return None
    text = clean_text(abs_html)
    # Crossref often prefixes "Abstract" or "<jats:title>Abstract</jats:title>"
    text = re.sub(r"^(?:Abstract|ABSTRACT|Summary)[:\s\.\-]*\s*", "", text)
    return text or None


# ------------------------------------------------------------------ main


def fetch_one(entry: dict) -> tuple[str | None, str | None]:
    """Return (abstract, source_label) or (None, None)."""
    pmid = entry.get("pmid")
    arxiv = entry.get("arxiv")
    doi = entry.get("doi")

    if pmid:
        text = fetch_pubmed(str(pmid).strip())
        if text:
            return text, "pubmed"
    if arxiv:
        text = fetch_arxiv(str(arxiv).strip())
        if text:
            return text, "arxiv"
    if doi:
        text = fetch_openalex(str(doi).strip())
        if text:
            return text, "openalex"
        text = fetch_crossref(str(doi).strip())
        if text:
            return text, "crossref"
    return None, None


def progress(stats: dict) -> None:
    print(
        f"  → {stats['fetched']} abstracts fetched, "
        f"{stats['pubmed']} from pubmed, "
        f"{stats['arxiv']} from arxiv, "
        f"{stats['openalex']} from openalex, "
        f"{stats['crossref']} from crossref, "
        f"{stats['skipped']} entries skipped"
    )


def main() -> int:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 100000  # keep long strings on one line
    yaml.indent(mapping=2, sequence=2, offset=0)

    data = yaml.load(DATA)
    total = len(data)
    print(f"Loaded {total} entries from {DATA}")

    stats = {
        "fetched": 0,
        "pubmed": 0,
        "arxiv": 0,
        "openalex": 0,
        "crossref": 0,
        "skipped": 0,
        "already": 0,
        "no_source": 0,
        "failed": [],
    }

    for i, entry in enumerate(data, 1):
        eid = entry.get("id") or entry.get("doi") or entry.get("pmid") or f"#{i}"
        if entry.get("abstract"):
            stats["already"] += 1
            continue
        if eid in SKIP_IDS:
            stats["skipped"] += 1
            continue
        if not any(entry.get(k) for k in ("pmid", "arxiv", "doi")):
            stats["no_source"] += 1
            stats["skipped"] += 1
            continue

        try:
            text, src = fetch_one(entry)
        except Exception as e:
            sys.stderr.write(f"  [{i}/{total}] {eid}: exception {e}\n")
            text, src = None, None

        if text and src:
            entry["abstract"] = text
            entry["abstract_source"] = src
            stats["fetched"] += 1
            stats[src] += 1
            print(f"  [{i}/{total}] {eid}: {src} ({len(text)} chars)")
        else:
            stats["skipped"] += 1
            stats["failed"].append(eid)
            print(f"  [{i}/{total}] {eid}: NO abstract")

        # Periodic progress
        if i % 25 == 0:
            progress(stats)
            # Checkpoint write
            yaml.dump(data, DATA)

    # Final write
    yaml.dump(data, DATA)

    print("\n=== Final ===")
    progress(stats)
    print(f"  already had abstract: {stats['already']}")
    print(f"  no PMID/arXiv/DOI: {stats['no_source']}")
    print(f"  failed list ({len(stats['failed'])}): {stats['failed']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
