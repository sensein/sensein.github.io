import { KnowledgeGraph, type JsonLdDocument } from "./kg.ts";
import { siteData, type SiteData } from "./extract.ts";
import graphJson from "../generated/sensein.jsonld?raw";

export type * from "./extract.ts";
import type {
  Publication,
  Project,
  TeamMember,
  NewsItem,
} from "./extract.ts";

/**
 * Site data, extracted from the lab knowledge graph.
 *
 * Every accessor below reads the compiled JSON-LD graph (src/lib/kg.ts,
 * written by scripts/kg/build.py) through siteData() in src/lib/extract.ts.
 * The shapes returned are the ones the pages have always used, so templates
 * did not have to change when the data moved from src/data/*.yml into kg/.
 */
let _kg: KnowledgeGraph | null = null;
export function graph(): KnowledgeGraph {
  if (!_kg) _kg = new KnowledgeGraph(JSON.parse(graphJson) as JsonLdDocument);
  return _kg;
}

/** Where the published JSON-LD context lives, and the base IRI for the
 *  site's relative links. These are the production addresses, so a page's
 *  embedded graph means the same thing wherever the page is served from. */
const KG_CONTEXT = "https://sensein.group/kg/context.jsonld";
const KG_BASE = "https://sensein.group/";

/** The slice of the graph about one or more records, for a page to embed
 *  as <script type="application/ld+json">. */
export function jsonldFor(...ids: (string | undefined)[]) {
  const docs = ids.filter((x): x is string => Boolean(x)).map((id) => graph().describe(id, KG_CONTEXT, KG_BASE));
  const seen = new Set<string>();
  const nodes = docs.flatMap((d) => d["@graph"]).filter((n) => {
    if (!n.id || seen.has(n.id)) return false;
    seen.add(n.id);
    return true;
  });
  return { "@context": [KG_CONTEXT, { "@base": KG_BASE }], "@graph": nodes };
}

/** A project's funding in one short line, such as "NIDA U24 DA064429",
 *  built from its grants, or its funding statement when it has none. */
export function fundingLine(p: Project): string | undefined {
  if (p.grants?.length) {
    return p.grants.map((g) => [g.funderShort ?? g.funder, g.award].filter(Boolean).join(" ")).join("; ");
  }
  return p.funder;
}

let _sd: SiteData | null = null;
function sd(): SiteData {
  if (!_sd) _sd = siteData(graph());
  return _sd;
}

export const teamMembers = () => sd().teamMembers();
export const students = () => sd().students();
export const alumniMembers = () => sd().alumniMembers();
export const collaborators = () => sd().collaborators();
export const projects = () => sd().projects();
export const publications = () => sd().publications();
export const publist = () => sd().publist();
export const news = () => sd().news();
export const publicationsPage = () => sd().publicationsPage();

/** Publications filtered to a given project slug, newest-first. */
export function publicationsForProject(slug: string): Publication[] {
  return publications()
    .filter((p) => (p.projects ?? []).includes(slug))
    .sort((a, b) => (b.year ?? 0) - (a.year ?? 0));
}

/**
 * Look up a publication by cross-reference id used in projects.yml. Accepts
 * DOIs ("10.x/y"), arXiv ids ("arXiv:2401.12345" or "arxiv:2401.12345"),
 * pmid:NNN, or slug:foo identifiers. Returns null if not found.
 */
let _pubIndex: Map<string, Publication> | null = null;
function pubIndex(): Map<string, Publication> {
  if (_pubIndex) return _pubIndex;
  const idx = new Map<string, Publication>();
  for (const p of publications()) {
    idx.set(p.id.toLowerCase(), p);
    if (p.doi) idx.set(p.doi.toLowerCase(), p);
    if (p.arxiv) {
      idx.set(`arxiv:${p.arxiv.toLowerCase()}`, p);
      idx.set(`10.48550/arxiv.${p.arxiv.toLowerCase()}`, p);
    }
    if (p.pmid) idx.set(`pmid:${p.pmid}`, p);
  }
  _pubIndex = idx;
  return idx;
}

export function findPublication(ref: string): Publication | null {
  return pubIndex().get(ref.trim().toLowerCase()) ?? null;
}

/** Collect publications cross-referenced by a project entry, in order. */
export function projectPublications(project: Project): Publication[] {
  if (!project.publications?.length) return [];
  const seen = new Set<string>();
  const out: Publication[] = [];
  for (const ref of project.publications) {
    const p = findPublication(ref);
    if (p && !seen.has(p.id)) {
      seen.add(p.id);
      out.push(p);
    }
  }
  return out;
}

/**
 * Educations entries are split across enumerated keys (education1..N).
 * Collapse them into a clean array for templates.
 */
export function memberEducations(m: TeamMember): string[] {
  const out: string[] = [];
  const keys: (keyof TeamMember)[] = [
    "education1",
    "education2",
    "education3",
    "education4",
    "education5",
  ];
  for (const k of keys) {
    const v = m[k];
    if (typeof v === "string" && v.trim()) out.push(v.trim());
  }
  return out;
}

/**
 * Parse loose YAML date strings like "2024 10 15" or "2024-10-15".
 * Bad/missing values return null.
 */
export function parseLooseDate(s: string | undefined): Date | null {
  if (!s) return null;
  const parts = s.trim().split(/[\s\-/]+/).map((p) => parseInt(p, 10));
  if (!parts.length || Number.isNaN(parts[0])) return null;
  const [y, m = 1, d = 1] = parts;
  return new Date(Date.UTC(y, Math.max(0, m - 1), d));
}

export function sortedNews(): NewsItem[] {
  return [...news()].sort((a, b) => {
    const da = parseLooseDate(a.date)?.getTime() ?? 0;
    const db = parseLooseDate(b.date)?.getTime() ?? 0;
    return db - da;
  });
}

/**
 * Stable URL-safe slug for a person's display name.
 * "Satrajit Ghosh" -> "satrajit-ghosh"
 */
export function personSlug(name: string): string {
  return name
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/** All team members across roster files, keyed by personSlug(name). */
let _peopleIndex: Map<string, TeamMember & { roster: "current" | "students" | "alumni" }> | null = null;
export function peopleIndex() {
  if (_peopleIndex) return _peopleIndex;
  const idx = new Map<string, TeamMember & { roster: "current" | "students" | "alumni" }>();
  for (const m of teamMembers()) idx.set(personSlug(m.name), { ...m, roster: "current" });
  for (const m of students()) idx.set(personSlug(m.name), { ...m, roster: "students" });
  for (const m of alumniMembers()) idx.set(personSlug(m.name), { ...m, roster: "alumni" });
  _peopleIndex = idx;
  return idx;
}

/**
 * Return the team-page anchor link for a contributor name, or null if the
 * person isn't in the roster files. Falls back to plain text rendering.
 */
export function personHref(name: string, baseUrl = "/team/"): string | null {
  const slug = personSlug(name);
  if (!peopleIndex().has(slug)) return null;
  return `${baseUrl}#${slug}`;
}
