import { withBase } from "./url";

const FALLBACK = "/images/placeholder-person.svg";

/**
 * Normalize a photo / image reference coming from YAML.
 * Originals include: protocol-relative (//host/…), bare http(s),
 * legacy relative (../images/foo.png), and root (/images/foo.png).
 */
export function normalizeImage(src: string | undefined | null): string {
  if (!src) return withBase(FALLBACK);
  const s = src.trim();
  if (!s) return withBase(FALLBACK);
  if (s.startsWith("//")) return `https:${s}`;
  if (/^https?:\/\//i.test(s)) return s;
  if (s.startsWith("../")) {
    return withBase(s.replace(/^(\.\.\/)+/, "/"));
  }
  return withBase(s.startsWith("/") ? s : `/${s}`);
}
