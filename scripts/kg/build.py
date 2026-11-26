#!/usr/bin/env python3
"""Compile the knowledge graph sources (kg/*.yaml) into RDF.

    python3 scripts/kg/build.py            # validate and write outputs
    python3 scripts/kg/build.py --check    # validate only

Steps:
  1. Merge every kg/*.yaml file into one KnowledgeGraph (schema/sensein.yaml).
  2. Check it against the schema: known slots only, required slots present,
     enum values valid, dates well formed, and every reference resolving to
     a node of the right class. Errors stop the build.
  3. Stamp provenance. Each record gets dcterms:modified from the last git
     commit that touched its lines, and the graph gets a prov:Activity for
     this build with the commit it ran on and the source files it read.
  4. Write the outputs:
       public/kg/sensein.jsonld   the graph as JSON-LD (served by the site)
       public/kg/context.jsonld   the JSON-LD context generated from the schema
       public/kg/sensein.ttl      the graph as Turtle (when rdflib is installed)
       build/kg/sensein.yaml      the merged LinkML data, for linkml-validate
       src/generated/sensein.jsonld  the copy the site build reads

The site reads only the JSON-LD graph. Loading the same graph into BrainKB
and exporting it again as JSON-LD with this context gives the site the same
input.

Needs Python 3.10+ and PyYAML. rdflib is optional and only used for Turtle.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schema" / "sensein.yaml"
KG = ROOT / "kg"
GRAPH_ID = "sid:graph/sensein"
SITE = "https://sensein.group"

BUILTIN_TYPES = {
    "string": "xsd:string",
    "integer": "xsd:integer",
    "boolean": "xsd:boolean",
    "datetime": "xsd:dateTime",
    "date": "xsd:date",
    "uri": "xsd:anyURI",
    "uriorcurie": "xsd:anyURI",
}


# ─── schema view ────────────────────────────────────────────────────────────


class Schema:
    def __init__(self, path: Path):
        self.raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.prefixes = self.raw["prefixes"]
        self.default_prefix = self.raw.get("default_prefix", "sensein")
        self.classes = self.raw["classes"]
        self.slots = self.raw["slots"]
        self.enums = self.raw.get("enums", {})
        self.types = self.raw.get("types", {})
        self.version = self.raw.get("version")

    def ancestors(self, cls: str) -> list[str]:
        out = [cls]
        while self.classes[out[-1]].get("is_a"):
            out.append(self.classes[out[-1]]["is_a"])
        return out

    def descendants(self, cls: str) -> set[str]:
        return {c for c in self.classes if cls in self.ancestors(c)}

    def class_slots(self, cls: str) -> OrderedDict:
        """Induced slot definitions for a class: the slot's own definition,
        overlaid with slot_usage from the class and its ancestors."""
        names: list[str] = []
        for a in reversed(self.ancestors(cls)):
            for s in self.classes[a].get("slots", []):
                if s not in names:
                    names.append(s)
        out = OrderedDict()
        for s in names:
            d = dict(self.slots[s])
            for a in reversed(self.ancestors(cls)):
                d.update(self.classes[a].get("slot_usage", {}).get(s, {}) or {})
            out[s] = d
        return out

    def class_uri(self, cls: str) -> str:
        return self.classes[cls].get("class_uri", f"{self.default_prefix}:{cls}")

    def rdf_types(self, cls: str) -> list[str]:
        """The class's own class_uri plus those its ancestors state."""
        out = []
        for a in self.ancestors(cls):
            c = self.classes[a]
            if a == cls or c.get("class_uri"):
                u = self.class_uri(a)
                if u not in out:
                    out.append(u)
        return out

    def slot_uri(self, slot: str) -> str:
        return self.slots[slot].get("slot_uri", f"{self.default_prefix}:{slot}")

    def has_identifier(self, cls: str) -> bool:
        return any(d.get("identifier") for d in self.class_slots(cls).values())

    def type_base(self, t: str) -> str:
        """The built-in type a schema type reduces to. A type whose own uri is
        xsd:anyURI counts as a uri even when it is typeof string, so that
        SiteUri values compile to IRIs."""
        while t in self.types:
            if self.types[t].get("uri") == "xsd:anyURI":
                return "uri"
            t = self.types[t].get("typeof", "string")
        return t

    def enum_iri(self, enum: str, value: str) -> str:
        pv = (self.enums[enum].get("permissible_values") or {}).get(value) or {}
        return pv.get("meaning") or f"{self.default_prefix}:{enum}/{value}"


# ─── loading ────────────────────────────────────────────────────────────────


def collection_slots(schema: Schema) -> dict[str, str]:
    """Container slot name -> class of its members."""
    out = {}
    for s, d in schema.class_slots("KnowledgeGraph").items():
        r = d.get("range")
        if r in schema.classes and d.get("multivalued"):
            out[s] = r
    return out


def load_sources(schema: Schema):
    colls = collection_slots(schema)
    merged: dict[str, list] = defaultdict(list)
    origin: dict[str, Path] = {}
    errors = []
    files = sorted(KG.glob("*.yaml"))
    for f in files:
        doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for key, items in doc.items():
            if key not in colls:
                errors.append(f"{f.name}: unknown collection '{key}'")
                continue
            for it in items or []:
                nid = it.get("id")
                if nid in origin:
                    errors.append(f"{f.name}: duplicate id {nid} (also in {origin[nid].name})")
                    continue
                origin[nid] = f
                merged[key].append(it)
    return files, merged, origin, errors


# ─── validation ─────────────────────────────────────────────────────────────

PARTIAL_DATE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
CURIE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*:\S+$")


class Validator:
    def __init__(self, schema: Schema, index: dict[str, tuple[str, dict]]):
        self.s = schema
        self.index = index
        self.errors: list[str] = []

    def err(self, where: str, msg: str):
        self.errors.append(f"{where}: {msg}")

    def node(self, cls: str, obj: dict, where: str):
        if not isinstance(obj, dict):
            self.err(where, f"expected a {cls} object")
            return
        slots = self.s.class_slots(cls)
        for k in obj:
            if k not in slots:
                self.err(where, f"'{k}' is not a slot of {cls}")
        for name, d in slots.items():
            v = obj.get(name)
            if v is None or v == [] or v == "":
                if d.get("required"):
                    self.err(where, f"{cls} requires '{name}'")
                continue
            if d.get("multivalued"):
                if not isinstance(v, list):
                    self.err(where, f"'{name}' must be a list")
                    continue
                for i, x in enumerate(v):
                    self.value(name, d, x, f"{where}.{name}[{i}]")
            else:
                if isinstance(v, list):
                    self.err(where, f"'{name}' takes one value, got a list")
                    continue
                self.value(name, d, v, f"{where}.{name}")

    def value(self, name: str, d: dict, v, where: str):
        r = d.get("range", self.s.raw.get("default_range", "string"))
        if d.get("identifier"):
            if not (isinstance(v, str) and CURIE.match(v)):
                self.err(where, f"identifier must be a CURIE, got {v!r}")
            return
        if r in self.s.classes:
            if self.s.has_identifier(r) and not (d.get("inlined") or d.get("inlined_as_list")):
                hit = self.index.get(v) if isinstance(v, str) else None
                if not hit:
                    self.err(where, f"reference {v!r} does not resolve")
                elif hit[0] not in self.s.descendants(r):
                    self.err(where, f"{v} is a {hit[0]}, expected {r}")
            else:
                self.node(r, v, where)
            return
        if r in self.s.enums:
            pvs = self.s.enums[r].get("permissible_values") or {}
            if v not in pvs:
                self.err(where, f"{v!r} is not one of {r}: {', '.join(pvs)}")
            return
        base = self.s.type_base(r)
        if r == "PartialDate" or (r in self.s.types and self.s.types[r].get("pattern")):
            pat = self.s.types[r].get("pattern")
            if not (isinstance(v, str) and re.match(pat, v)):
                self.err(where, f"{v!r} does not match {r} ({pat})")
            return
        if base == "integer":
            if not isinstance(v, int) or isinstance(v, bool):
                self.err(where, f"expected an integer, got {v!r}")
            elif "minimum_value" in d and v < d["minimum_value"]:
                self.err(where, f"{v} is below the minimum {d['minimum_value']}")
            return
        if base == "uri":
            # Absolute URLs, or paths on the site itself ("/riverst/").
            if not (isinstance(v, str) and re.match(r"^([a-z][a-z0-9+.-]*://|/)", v)):
                self.err(where, f"expected a URL or a site path, got {v!r}")
            return
        if base == "uriorcurie":
            if not (isinstance(v, str) and (CURIE.match(v))):
                self.err(where, f"expected a URI or CURIE, got {v!r}")
            return
        if base == "datetime":
            return
        if not isinstance(v, (str, int, float)):
            self.err(where, f"expected text, got {type(v).__name__}")
        if d.get("pattern") and isinstance(v, str) and not re.match(d["pattern"], v):
            self.err(where, f"{v!r} does not match {d['pattern']}")


# ─── provenance ─────────────────────────────────────────────────────────────


def git(*args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def blame_dates(path: Path) -> list[str | None]:
    """Commit date (YYYY-MM-DD) of every line of a file, from git blame.
    Lines not yet committed get today's date."""
    out = git("blame", "--line-porcelain", "--", str(path.relative_to(ROOT)))
    if not out:
        return []
    dates, current = [], None
    for line in out.splitlines():
        if line.startswith("committer-time "):
            current = dt.datetime.fromtimestamp(int(line.split()[1]), dt.timezone.utc).date().isoformat()
        elif line.startswith("\t"):
            dates.append(current)
    return dates


def record_modified(files: list[Path]) -> dict[str, str]:
    """id -> date of the latest commit touching the record's lines."""
    out: dict[str, str] = {}
    for f in files:
        lines = f.read_text(encoding="utf-8").splitlines()
        dates = blame_dates(f)
        if len(dates) != len(lines):
            continue
        current = None
        for line, date in zip(lines, dates):
            m = re.match(r"^- id:\s*(\S+)", line)
            if m:
                current = m.group(1).strip("'\"")
            elif line and not line.startswith((" ", "-", "#")):
                current = None
            if current and date and line.strip():
                if date > out.get(current, ""):
                    out[current] = date
    return out


def build_activity(files: list[Path]) -> dict:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    sha = os.environ.get("GITHUB_SHA") or git("rev-parse", "HEAD").strip() or "uncommitted"
    used = []
    for f in files:
        rel = str(f.relative_to(ROOT))
        last = git("log", "-1", "--format=%H %cI", "--", rel).split()
        entry = {
            "id": f"sid:source/{rel}",
            "path": rel,
            "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
        }
        if len(last) == 2:
            entry["commit"], entry["last_changed"] = last
        used.append(entry)
    return {
        "id": f"sid:build/{sha[:12]}-{now.strftime('%Y%m%dT%H%M%SZ')}",
        "started_at": now.isoformat(),
        "commit": sha,
        "software_agent": "scripts/kg/build.py",
        "used": used,
    }


# ─── JSON-LD ────────────────────────────────────────────────────────────────


def make_context(s: Schema) -> dict:
    ctx: dict = {"@version": 1.1, "@base": SITE + "/"}
    for p, iri in s.prefixes.items():
        ctx[p] = iri
    ctx["id"] = "@id"
    ctx["type"] = "@type"
    for name, d in s.slots.items():
        if d.get("identifier"):
            continue
        r = d.get("range", "string")
        term: dict = {"@id": s.slot_uri(name)}
        if r in s.classes:
            if s.has_identifier(r) and not (d.get("inlined") or d.get("inlined_as_list")):
                term["@type"] = "@id"
        elif r in s.enums:
            term["@type"] = "@vocab"
            term["@context"] = {
                v: s.enum_iri(r, v) for v in (s.enums[r].get("permissible_values") or {})
            }
        else:
            base = s.type_base(r)
            if base in ("uri", "uriorcurie"):
                term["@type"] = "@id"
            elif base == "integer":
                term["@type"] = "xsd:integer"
            elif base == "datetime":
                term["@type"] = "xsd:dateTime"
        ctx[name] = term
    return ctx


def partial_date(v: str) -> dict:
    t = {4: "xsd:gYear", 7: "xsd:gYearMonth", 10: "xsd:date"}[len(v)]
    return {"@value": v, "@type": t}


def to_jsonld(s: Schema, cls: str, obj: dict) -> dict:
    out: dict = OrderedDict()
    slots = s.class_slots(cls)
    if "id" in obj:
        out["id"] = obj["id"]
    out["type"] = s.rdf_types(cls)
    for name, d in slots.items():
        if d.get("identifier") or name not in obj:
            continue
        v = obj[name]
        r = d.get("range", "string")

        def conv(x):
            if r in s.classes and (d.get("inlined") or d.get("inlined_as_list") or not s.has_identifier(r)):
                return to_jsonld(s, r, x)
            if r == "PartialDate":
                return partial_date(x)
            return x

        out[name] = [conv(x) for x in v] if isinstance(v, list) else conv(v)
    return out


# ─── main ───────────────────────────────────────────────────────────────────


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="validate only, write nothing")
    args = ap.parse_args(argv)

    s = Schema(SCHEMA)
    colls = collection_slots(s)
    files, merged, origin, errors = load_sources(s)

    index: dict[str, tuple[str, dict]] = {}
    for coll, items in merged.items():
        for it in items:
            index[it["id"]] = (colls[coll], it)

    v = Validator(s, index)
    for coll, items in merged.items():
        for it in items:
            v.node(colls[coll], it, f"{origin[it['id']].name}:{it.get('id')}")
    errors += v.errors
    if errors:
        for e in errors:
            print("error:", e, file=sys.stderr)
        print(f"{len(errors)} error(s); the graph was not built.", file=sys.stderr)
        return 1

    counts = {k: len(merged[k]) for k in colls if merged.get(k)}
    print("graph ok:", ", ".join(f"{k} {n}" for k, n in counts.items()))
    if args.check:
        return 0

    modified = record_modified(files)
    for items in merged.values():
        for it in items:
            if "modified" not in it and it["id"] in modified:
                it["modified"] = modified[it["id"]]

    activity = build_activity(files)
    graph = OrderedDict()
    graph["id"] = GRAPH_ID
    graph["title"] = "Senseable Intelligence Group knowledge graph"
    graph["description"] = (
        "People, projects, funding, publications, images, topics and news of the "
        "Senseable Intelligence Group, compiled from the sources in the "
        "sensein/sensein.github.io repository."
    )
    graph["version"] = s.version
    graph["license"] = "https://creativecommons.org/licenses/by/4.0/"
    graph["was_generated_by"] = activity
    container = OrderedDict(graph)
    for k in colls:
        if merged.get(k):
            container[k] = merged[k]

    # Merged LinkML data, for linkml-validate.
    out_yaml = ROOT / "build" / "kg" / "sensein.yaml"
    out_yaml.parent.mkdir(parents=True, exist_ok=True)
    out_yaml.write_text(
        yaml.safe_dump(json.loads(json.dumps(container)), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    # JSON-LD: every node with an id at the top level of @graph, the graph's
    # own description first.
    ctx = make_context(s)
    nodes = [to_jsonld(s, "KnowledgeGraph", {k: v for k, v in graph.items()})]
    for k in colls:
        for it in merged.get(k, []):
            nodes.append(to_jsonld(s, colls[k], it))
    doc = {"@context": ctx, "@graph": nodes}

    targets = [ROOT / "public" / "kg", ROOT / "src" / "generated"]
    for t in targets:
        t.mkdir(parents=True, exist_ok=True)
    text = json.dumps(doc, ensure_ascii=False, indent=1)
    (ROOT / "public" / "kg" / "sensein.jsonld").write_text(text, encoding="utf-8")
    (ROOT / "src" / "generated" / "sensein.jsonld").write_text(text, encoding="utf-8")
    (ROOT / "public" / "kg" / "context.jsonld").write_text(
        json.dumps({"@context": ctx}, ensure_ascii=False, indent=1), encoding="utf-8")

    try:
        import rdflib  # noqa: F401
    except ImportError:
        print("rdflib not installed; skipped Turtle output")
    else:
        g = rdflib.Graph()
        g.parse(data=text, format="json-ld")
        for p, iri in s.prefixes.items():
            g.bind(p, iri, override=True)
        (ROOT / "public" / "kg" / "sensein.ttl").write_text(g.serialize(format="turtle"), encoding="utf-8")
        print(f"wrote public/kg/sensein.ttl ({len(g)} triples)")
    print("wrote public/kg/sensein.jsonld, public/kg/context.jsonld, build/kg/sensein.yaml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
