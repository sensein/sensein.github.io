#!/usr/bin/env python3
"""Localize and standardise team-member profile photos.

For every entry in team_members.yml, students.yml, alumni_members.yml:
  - If `photo:` is external (http://, https://, //) → download.
  - Crop to a centred square, resize to 320x320, save as WebP.
  - Store at `public/images/people/<personSlug>.webp` (slug derived from name).
  - Rewrite `photo:` to the local path.
Idempotent: skips entries already pointing at /images/people/...

Run from repo root:  python3 scripts/localize-photos.py
"""
from __future__ import annotations

import io
import re
import sys
import urllib.request
import urllib.parse
from pathlib import Path

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "images" / "people"
OUT.mkdir(parents=True, exist_ok=True)

ROSTERS = [
    ROOT / "src" / "data" / "team_members.yml",
    ROOT / "src" / "data" / "students.yml",
    ROOT / "src" / "data" / "alumni_members.yml",
]

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
TIMEOUT = 25
SIZE = 320  # square px


def person_slug(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def normalize_url(src: str) -> str | None:
    s = (src or "").strip()
    if not s:
        return None
    if s.startswith("//"):
        return "https:" + s
    if s.startswith("/") or s.startswith("../"):
        return None  # already local
    if s.startswith("http://") or s.startswith("https://"):
        return s
    return None


def download(url: str) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.read()
    except Exception as e:
        print(f"    ✗ download failed: {e}", file=sys.stderr)
        return None


def standardise(raw: bytes) -> bytes | None:
    """Crop centred-square, resize to SIZE × SIZE, return WebP bytes."""
    try:
        img = Image.open(io.BytesIO(raw))
    except Exception as e:
        print(f"    ✗ PIL open failed: {e}", file=sys.stderr)
        return None
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((SIZE, SIZE), Image.LANCZOS)
    buf = io.BytesIO()
    if img.mode == "RGBA":
        img.save(buf, format="WEBP", quality=82, method=6, alpha_quality=80)
    else:
        img.save(buf, format="WEBP", quality=82, method=6)
    return buf.getvalue()


def localize_for_member(member: dict) -> bool:
    """Returns True if the member's photo was updated."""
    photo = member.get("photo")
    if not photo:
        return False
    local_target = OUT / f"{person_slug(member['name'])}.webp"
    rel = f"/images/people/{local_target.name}"
    # Already-local pointing at our managed file — skip
    if str(photo).strip() == rel and local_target.exists():
        return False
    src_url = normalize_url(str(photo))
    if src_url is None:
        # Already local but at a different path → re-process if file is readable
        legacy = Path(str(photo).lstrip("/")) if str(photo).startswith("/") else None
        candidates = []
        if legacy:
            candidates.append(ROOT / "public" / str(legacy))
        # Handle ../images/foo.jpg
        if "../images/" in str(photo):
            candidates.append(ROOT / "public" / str(photo).split("../", 1)[1])
        # Anything we can find?
        for c in candidates:
            if c.exists():
                try:
                    raw = c.read_bytes()
                    out = standardise(raw)
                    if out:
                        local_target.write_bytes(out)
                        member["photo"] = rel
                        print(f"    ✓ rebuilt locally  {member['name']}  →  {rel}")
                        return True
                except Exception as e:
                    print(f"    ✗ local read failed for {c}: {e}", file=sys.stderr)
        return False
    raw = download(src_url)
    if not raw:
        return False
    out = standardise(raw)
    if not out:
        return False
    local_target.write_bytes(out)
    member["photo"] = rel
    print(f"    ✓ {member['name']}  {len(out):>6}b  →  {rel}")
    return True


def main() -> int:
    total = 0
    updated = 0
    for path in ROSTERS:
        if not path.exists():
            continue
        print(f"\n# {path.relative_to(ROOT)}")
        text = path.read_text()
        members = yaml.safe_load(text) or []
        if not isinstance(members, list):
            print("  skip — not a list")
            continue
        any_changed = False
        for m in members:
            if not isinstance(m, dict) or not m.get("name"):
                continue
            total += 1
            if localize_for_member(m):
                updated += 1
                any_changed = True
        if any_changed:
            path.write_text(yaml.safe_dump(members, sort_keys=False, allow_unicode=True, width=10**9))
            print(f"  → wrote back {path.name}")
    print(f"\nTotal members: {total}; photos localised this run: {updated}")
    print(f"Files in {OUT.relative_to(ROOT)}: {sum(1 for _ in OUT.iterdir())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
