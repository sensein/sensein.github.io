import yaml from "js-yaml";

const RAW_FILES = import.meta.glob<string>("../data/*.yml", {
  eager: true,
  query: "?raw",
  import: "default",
});

export interface TeamMember {
  name: string;
  photo?: string;
  info?: string;
  email?: string;
  /** GitHub username only (no URL). */
  github?: string;
  linkedin?: string;
  website?: string;
  scholar?: string;
  orcid?: string;
  /** Twitter/X handle (with or without leading @). */
  twitter?: string;
  /** Bluesky handle (e.g. user.bsky.social). */
  bluesky?: string;
  duration?: string;
  number_educ?: number;
  education1?: string;
  education2?: string;
  education3?: string;
  education4?: string;
  education5?: string;
}

export interface CollaboratorPerson {
  name: string;
}

export interface CollaboratorGroup {
  home: string;
  persons: CollaboratorPerson[];
}

export interface ProjectLink {
  label?: string;
  url?: string;
}

export interface ProjectContributors {
  current?: string[];
  former?: string[];
  /** External collaborators (non-lab). Plain text, optionally "Name (Affiliation)". */
  external?: string[];
}

export interface Project {
  slug: string;
  title: string;
  status: "active" | "former";
  description?: string;
  funder?: string;
  image?: string;
  themes?: string[];
  links?: ProjectLink[];
  contributors?: ProjectContributors;
  /** Cross-reference IDs into publications.yml (DOIs, arXiv ids). */
  publications?: string[];
}

/** Summary of a preprint precursor attached to a published-of-record entry. */
export interface PreprintRef {
  id: string;
  venue?: string;
  url?: string;
  year?: number;
  doi?: string;
  arxiv?: string;
}

/** Coarse-grained kind of article — orthogonal to `type` (the publication form). */
export type PublicationCategory =
  | "original-research"
  | "methods"
  | "software"
  | "review"
  | "perspective"
  | "commentary"
  | "editorial"
  | "dataset"
  | "benchmark"
  | "tutorial";

/** Schema for the curated publications corpus in src/data/publications.yml. */
export interface Publication {
  id: string;
  type: "journal" | "preprint" | "conference" | "chapter" | "workshop" | "software" | "patent" | "dataset";
  category: PublicationCategory;
  year: number;
  title: string;
  authors: string[];
  venue?: string;
  doi?: string;
  pmid?: string;
  pmcid?: string;
  arxiv?: string;
  url?: string;
  pdf_url?: string;
  github?: string;
  sources?: string[];
  projects?: string[];
  lab_authors?: string[];
  topics: string[];
  /** Preprint precursor(s) that have been superseded by this published-of-record
   *  entry. Only present on the journal/conference/chapter record. */
  preprints?: PreprintRef[];
  cited_by?: number;
  /** Abstract pulled verbatim from PubMed / PMC / arXiv / OpenAlex / Crossref.
      No paraphrasing — only authoritative sources. */
  abstract?: string;
  abstract_source?: "pubmed" | "pmc" | "arxiv" | "openalex" | "crossref" | "publisher";
  /** 1–3 sentence summary of the paper's main contribution. Derived directly
      from the abstract; never invented when the abstract is absent. */
  key_findings?: string;
}

/** Legacy schema for src/data/publist.yml (the manually-curated highlights). */
export interface FeaturedPublication {
  title: string;
  image?: string;
  description?: string;
  authors?: string;
  type?: string;
  date?: string;
  link?: { url?: string; display?: string };
  "code link"?: { url?: string; display?: string };
  highlight?: number;
  news1?: string;
  news2?: string;
}

export interface NewsItem {
  date: string;
  headline: string;
}

function load<T>(name: string): T {
  const key = `../data/${name}`;
  const raw = RAW_FILES[key];
  if (typeof raw !== "string") {
    throw new Error(
      `Data file not found: ${name}. Available: ${Object.keys(RAW_FILES).join(", ")}`,
    );
  }
  return yaml.load(raw) as T;
}

function loadArray<T>(name: string): T[] {
  const v = load<T[] | null>(name);
  return Array.isArray(v) ? v : [];
}

export const teamMembers = () => loadArray<TeamMember>("team_members.yml");
export const students = () => loadArray<TeamMember>("students.yml");
export const alumniMembers = () => loadArray<TeamMember>("alumni_members.yml");
export const collaborators = () =>
  loadArray<CollaboratorGroup>("collaborators.yml");
export const projects = () => loadArray<Project>("projects.yml");
export const publications = () => loadArray<Publication>("publications.yml");
export const publist = () => loadArray<FeaturedPublication>("publist.yml");
export const news = () => loadArray<NewsItem>("news.yml");

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
