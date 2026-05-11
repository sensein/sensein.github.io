const RAW_BASE = import.meta.env.BASE_URL ?? "/";
const BASE = RAW_BASE.endsWith("/") ? RAW_BASE.slice(0, -1) : RAW_BASE;

export function withBase(path: string): string {
  if (!path) return BASE || "/";
  if (/^([a-z]+:)?\/\//i.test(path) || path.startsWith("mailto:")) {
    return path;
  }
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${BASE}${p}`;
}

export function isActive(currentPath: string, target: string): boolean {
  const stripped = currentPath.replace(BASE, "") || "/";
  const t = target === "/" ? "/" : target.replace(/\/$/, "");
  const c = stripped === "/" ? "/" : stripped.replace(/\/$/, "");
  if (t === "/") return c === "/";
  return c === t || c.startsWith(`${t}/`);
}
