#!/usr/bin/env python3
"""Validate the site's YAML data files against the LinkML schema.

Each file in src/data/ is a bare list of records (or, for publications_page,
a single object). We validate every record against its target class using
LinkML's programmatic validator and exit non-zero if any ERROR-severity
result is found.

    python schema/validate_data.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml
from linkml.validator import validate

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schema" / "sensein.yaml"
DATA = ROOT / "src" / "data"

# file -> (target class, is the file a single object rather than a list?)
FILES: dict[str, tuple[str, bool]] = {
    "team_members.yml": ("TeamMember", False),
    "students.yml": ("TeamMember", False),
    "alumni_members.yml": ("TeamMember", False),
    "collaborators.yml": ("Collaborator", False),
    "projects.yml": ("Project", False),
    "publications.yml": ("Publication", False),
    "publist.yml": ("FeaturedPublication", False),
    "news.yml": ("NewsItem", False),
    "publications_page.yml": ("PublicationsPage", True),
}


def main() -> int:
    total_errors = 0
    total_records = 0

    for fname, (target_class, is_object) in FILES.items():
        path = DATA / fname
        if not path.exists():
            print(f"⚠  {fname}: not found, skipping")
            continue

        doc = yaml.safe_load(path.read_text())
        if doc is None:
            print(f"✓  {fname}: empty ({target_class})")
            continue

        records = [doc] if is_object else doc
        if not isinstance(records, list):
            print(f"✗  {fname}: expected a list of {target_class}, got {type(doc).__name__}")
            total_errors += 1
            continue

        file_errors = 0
        for i, record in enumerate(records):
            report = validate(record, str(SCHEMA), target_class)
            for result in report.results:
                if str(result.severity).upper().endswith("ERROR"):
                    file_errors += 1
                    total_errors += 1
                    label = record.get("id") or record.get("slug") or record.get("name") or f"index {i}"
                    print(f"✗  {fname}[{label}]: {result.message}")
        total_records += len(records)
        mark = "✓" if file_errors == 0 else "✗"
        print(f"{mark}  {fname}: {len(records)} record(s) validated against {target_class}, {file_errors} error(s)")

    print(f"\n{'─' * 60}")
    if total_errors:
        print(f"FAILED: {total_errors} validation error(s) across {total_records} records.")
        return 1
    print(f"OK: all {total_records} records conform to the schema.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
