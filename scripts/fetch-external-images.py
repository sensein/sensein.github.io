#!/usr/bin/env python3
"""
Walk src/data/*.yml and src/components/Hero.astro, download every external image
reference (http, https, or protocol-relative //) into public/images/external/
with a stable safe filename, and rewrite the references to local paths.

Idempotent: re-running skips URLs that are already mapped to a local file.
"""
import hashlib
import os
import re
import sys
import urllib.request
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "src" / "data"
HERO = ROOT / "src" / "components" / "Hero.astro"
OUT_DIR = ROOT / "public" / "images" / "external"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL_RE = re.compile(r'(https?://[^\s"\']+|//[A-Za-z][^\s"\']+)')

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
TIMEOUT = 20


def normalize(url: str) -> str:
    if url.startswith("//"):
        return "https:" + url
    return url


def safe_name(url: str) -> str:
    """Stable filename derived from URL: <basename>-<short-hash>.<ext>."""
    parsed = urllib.parse.urlparse(normalize(url))
    path = parsed.path
    base = os.path.basename(path) or "image"
    # Strip query params and decode percent-escapes for legibility.
    base = urllib.parse.unquote(base)
    # Replace odd chars.
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    # Cap length.
    name, ext = os.path.splitext(base)
    if len(name) > 40:
        name = name[:40]
    if not ext or len(ext) > 6:
        ext = ".img"
    h = hashlib.sha1(url.encode()).hexdigest()[:8]
    return f"{name}-{h}{ext}"


def detect_ext(content_type: str | None, fallback: str) -> str:
    if not content_type:
        return fallback
    ct = content_type.split(";")[0].strip().lower()
    return {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
        "image/x-icon": ".ico",
        "image/tiff": ".tif",
    }.get(ct, fallback)


def download(url: str) -> Path | None:
    target = OUT_DIR / safe_name(url)
    if target.exists() and target.stat().st_size > 0:
        return target
    try:
        req = urllib.request.Request(normalize(url), headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = r.read()
            ct = r.headers.get("Content-Type")
        # Fix extension if the response disagrees with the filename guess.
        better_ext = detect_ext(ct, target.suffix)
        if better_ext and target.suffix != better_ext:
            target = target.with_suffix(better_ext)
            if target.exists() and target.stat().st_size > 0:
                return target
        target.write_bytes(data)
        print(f"  ✓ {len(data):>7}b  {url}  →  {target.relative_to(ROOT)}")
        return target
    except Exception as e:
        print(f"  ✗ FAILED  {url}  ({e})")
        return None


def collect_urls() -> list[tuple[Path, str]]:
    """Return list of (file, url) for every external image reference."""
    found: list[tuple[Path, str]] = []
    for yml in sorted(DATA_DIR.glob("*.yml")):
        text = yml.read_text()
        for line in text.splitlines():
            if line.lstrip().startswith("#"):
                continue
            if not re.search(r"^\s*(photo|image)\s*:", line):
                continue
            for m in URL_RE.finditer(line):
                found.append((yml, m.group(0)))
    hero = HERO.read_text()
    for m in URL_RE.finditer(hero):
        # Skip URLs that aren't image-y.
        if any(
            ext in m.group(0).lower()
            for ext in (
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp",
                ".svg",
                ".tif",
                ".tiff",
                "/default.jpg",
            )
        ):
            found.append((HERO, m.group(0)))
    return found


def main() -> int:
    mapping: dict[str, str] = {}
    refs = collect_urls()
    uniq = sorted({u for _, u in refs})
    print(f"Found {len(refs)} references ({len(uniq)} unique URLs)\n")
    for url in uniq:
        p = download(url)
        if p:
            mapping[url] = "/" + str(p.relative_to(ROOT / "public")).replace(os.sep, "/")

    if not mapping:
        print("No URLs were successfully downloaded.")
        return 0

    print("\nRewriting source files…")
    files = sorted({f for f, _ in refs})
    # Replace longest URLs first so a protocol-relative substring inside an
    # https:// URL doesn't get rewritten first and leave a stray "https:".
    ordered = sorted(mapping.items(), key=lambda kv: -len(kv[0]))
    for f in files:
        original = f.read_text()
        updated = original
        for url, local in ordered:
            updated = updated.replace(url, local)
        if updated != original:
            f.write_text(updated)
            print(f"  • {f.relative_to(ROOT)}")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
