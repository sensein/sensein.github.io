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

export interface Project {
  title: string;
  image?: string;
  description?: string;
  authors?: string;
  link?: { url?: string; display?: string };
  highlight?: number;
  news1?: string;
  news2?: string;
}

export interface Publication {
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

export const teamMembers = () => load<TeamMember[]>("team_members.yml");
export const students = () => load<TeamMember[]>("students.yml");
export const alumniMembers = () => load<TeamMember[]>("alumni_members.yml");
export const collaborators = () =>
  load<CollaboratorGroup[]>("collaborators.yml");
export const projects = () => load<Project[]>("projects.yml");
export const papers = () => load<Publication[]>("papers.yml");
export const publist = () => load<Publication[]>("publist.yml");
export const news = () => load<NewsItem[]>("news.yml");

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
  return new Date(y, Math.max(0, m - 1), d);
}

export function sortedNews(): NewsItem[] {
  return [...news()].sort((a, b) => {
    const da = parseLooseDate(a.date)?.getTime() ?? 0;
    const db = parseLooseDate(b.date)?.getTime() ?? 0;
    return db - da;
  });
}
