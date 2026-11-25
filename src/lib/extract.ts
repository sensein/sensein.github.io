/**
 * Extraction of the site's data from the lab knowledge graph.
 *
 * siteData(kg) returns the records the pages use, in the shapes they have
 * always used (the v1 YAML shapes), read from a KnowledgeGraph. It has no
 * Astro or Vite dependencies, so build scripts can use it too
 * (scripts/build-search-embeddings.mjs).
 */
import { KnowledgeGraph, T, many, num, str, type KGNode } from "./kg.ts";

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

/** A person we've collaborated with. Person-centric: one entry per
 *  human, with their current institutional home plus the named lab
 *  projects / ecosystem efforts they participated in and rough years.
 *  Project tags mix slugs from projects.yml (e.g. "sails", "bican-um1")
 *  with ecosystem-effort names not modelled as standalone projects
 *  (e.g. "BANDA", "BIDS", "fMRIPrep"). */
export interface Collaborator {
  name: string;
  /** Current home institution, e.g. "MGH Martinos Center" or "Stanford". */
  current_institution?: string;
  /** Lab projects + ecosystem efforts they contributed to. */
  projects?: string[];
  /** Rough year span of the collaboration, e.g. "2018–present" or "2003–2014". */
  years?: string;
  /** Optional one-line note (role, sub-project, etc.). */
  note?: string;
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

/** A publication as the pages use it, extracted from the graph. */
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

/** A highlighted publication (the curated highlights list), extracted from the graph. */
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

/** Editable content of /publications/ (v1 publications_page.yml). */
export interface TopicArea {
  label: string;
  tag: string;
  description?: string;
}
export interface PublicationsPage {
  summary?: string;
  keywords?: string[];
  topics: TopicArea[];
}

export interface SiteData {
  teamMembers(): TeamMember[];
  students(): TeamMember[];
  alumniMembers(): TeamMember[];
  collaborators(): Collaborator[];
  projects(): Project[];
  publications(): Publication[];
  publist(): FeaturedPublication[];
  news(): NewsItem[];
  publicationsPage(): PublicationsPage;
}

export function siteData(kg: KnowledgeGraph): SiteData {
  const LAB = "sid:org/sensein";

  function imageUrl(kg: KnowledgeGraph, node: KGNode | undefined): string | undefined {
    return str(kg.ref(node, "image")?.content_url);
  }

  function account(person: KGNode, service: string): KGNode | undefined {
    return many<KGNode>(person.accounts).find((a) => a.service === service);
  }

  /** v1 roster entry for one membership. */
  function rosterEntry(kg: KnowledgeGraph, ms: KGNode): TeamMember {
    const p = kg.ref(ms, "member")!;
    const m: TeamMember = { name: str(p.name)! };
    const photo = imageUrl(kg, p);
    if (photo) m.photo = photo;
    const info = str(ms.role_title);
    if (info) m.info = info;
    const email = str(p.email);
    if (email) m.email = email;
    const gh = account(p, "github");
    if (gh) m.github = str(gh.account_name);
    const li = account(p, "linkedin");
    if (li) m.linkedin = str(li.url);
    const site = str(p.url);
    if (site) m.website = site;
    const sch = account(p, "google_scholar");
    if (sch) m.scholar = str(sch.url);
    const orcid = str(p.orcid);
    if (orcid) m.orcid = orcid.replace(/^ORCID:/, "");
    const x = account(p, "x");
    if (x) m.twitter = `@${str(x.account_name)}`;
    const bs = account(p, "bluesky");
    if (bs) m.bluesky = str(bs.account_name);
    const period = str(ms.period_text);
    if (period) m.duration = period;
    const edu = many<KGNode>(p.education).map((e) => str(e.statement)!);
    const cv = str(p.cv);
    if (cv) edu.push(`<a href="${cv}">Full CV</a>`);
    if (edu.length) m.number_educ = edu.length;
    edu.slice(0, 5).forEach((e, i) => {
      (m as unknown as Record<string, unknown>)[`education${i + 1}`] = e;
    });
    return m;
  }

  function roster(status: "current" | "former", section?: "members" | "students"): TeamMember[] {
    return kg
      .ofType(T.Membership)
      .filter((ms) => ms.organization === LAB && ms.membership_status === status)
      .filter((ms) => !section || (ms.roster_section ?? "members") === section)
      .sort((a, b) => (num(a.roster_order) ?? 0) - (num(b.roster_order) ?? 0))
      .map((ms) => rosterEntry(kg, ms));
  }

  function labProjects(): KGNode[] {
    return kg
      .ofType(T.Project)
      .filter((p) => p.project_type === "lab_project");
  }

  function pubSlug(n: KGNode): string {
    return str(n.slug)!;
  }

  let _projects: Project[] | null = null;
  let _publications: Publication[] | null = null;

  const teamMembers = () => roster("current", "members");
  const students = () => roster("current", "students");
  const alumniMembers = () => roster("former");

  const collaborators = (): Collaborator[] => {
    return kg.ofType(T.Collaboration).map((c) => {
      const person = kg.ref(c, "collaborator")!;
      const out: Collaborator = { name: str(person.name)! };
      const inst = kg.ref(person, "affiliations");
      if (inst) out.current_institution = str(inst.name);
      const projs = kg
        .refs(c, "projects")
        .map((p) => (p.project_type === "lab_project" ? str(p.slug)! : str(p.title)!));
      if (projs.length) out.projects = projs;
      const years = str(c.period_text);
      if (years) out.years = years;
      const note = str(c.note);
      if (note) out.note = note;
      return out;
    });
  };

  const projects = (): Project[] => {
    if (_projects) return _projects;
    _projects = labProjects().map((p) => {
      const out: Project = {
        slug: str(p.slug)!,
        title: str(p.title)!,
        status: (str(p.project_status) ?? "active") as Project["status"],
      };
      const desc = str(p.description);
      if (desc) out.description = desc;
      const funder = str(p.funding_statement);
      if (funder) out.funder = funder;
      const img = imageUrl(kg, p);
      if (img) out.image = img;
      out.themes = kg.refs(p, "themes").map((t) => str(t.notation)!);
      out.links = many<KGNode>(p.links).map((l) => {
        const link: ProjectLink = {};
        const label = str(l.label);
        if (label) link.label = label;
        link.url = str(l.url);
        return link;
      });
      const names = (slot: string) => kg.refs(p, slot).map((x) => str(x.name)!);
      out.contributors = { current: names("members"), former: names("former_members") };
      const ext = many<unknown>(p.external_contributors).map((x) => str(x)!);
      if (ext.length) out.contributors.external = ext;
      out.publications = kg.refs(p, "anchor_publications").map(pubSlug);
      return out;
    });
    return _projects;
  };

  const publications = (): Publication[] => {
    if (_publications) return _publications;
    _publications = kg.ofType(T.Publication).map((n) => {
      const authors = many<KGNode>(n.authorships)
        .slice()
        .sort((a, b) => (num(a.position) ?? 0) - (num(b.position) ?? 0))
        .map((a) => str(a.author_name)!);
      const out: Publication = {
        id: pubSlug(n),
        type: str(n.publication_type) as Publication["type"],
        category: str(n.category) as PublicationCategory,
        year: num(n.year)!,
        title: str(n.title)!,
        authors,
        topics: kg.refs(n, "topics").map((t) => str(t.notation)!),
      };
      for (const k of ["venue", "doi", "pmid", "pmcid", "arxiv", "url", "pdf_url"] as const) {
        const v = str(n[k]);
        if (v) out[k] = v;
      }
      const code = str(n.code_repository);
      if (code) out.github = code.replace(/^https:\/\/github\.com\//, "");
      const sources = many<unknown>(n.derived_from)
        .map((x) => str(x)!)
        .filter((x) => x !== "site-yaml-v1");
      if (sources.length) out.sources = sources;
      const projs = kg.refs(n, "projects").map((p) => str(p.slug)!);
      if (projs.length) out.projects = projs;
      out.lab_authors = kg.refs(n, "lab_authors").map((p) => str(p.name)!);
      const pre = many<KGNode>(n.preprints).map((q) => {
        const r: PreprintRef = { id: str(q.identifier)! };
        const venue = str(q.venue);
        if (venue) r.venue = venue;
        const url = str(q.url);
        if (url) r.url = url;
        const year = num(q.year);
        if (year !== undefined) r.year = year;
        const doi = str(q.doi);
        if (doi) r.doi = doi;
        const arxiv = str(q.arxiv);
        if (arxiv) r.arxiv = arxiv;
        return r;
      });
      if (pre.length) out.preprints = pre;
      const cited = num(n.cited_by_count);
      if (cited !== undefined) out.cited_by = cited;
      const abs = str(n.abstract);
      if (abs) out.abstract = abs;
      const absSrc = str(n.abstract_source);
      if (absSrc) out.abstract_source = absSrc as Publication["abstract_source"];
      const kf = str(n.key_findings);
      if (kf) out.key_findings = kf;
      return out;
    });
    return _publications;
  };

  /** Featured publications (v1 publist.yml), from each Publication's highlight. */
  const publist = (): FeaturedPublication[] => {
    return kg
      .ofType(T.Publication)
      .filter((n) => n.highlight)
      .sort(
        (a, b) =>
          (num((a.highlight as KGNode).rank) ?? 0) - (num((b.highlight as KGNode).rank) ?? 0),
      )
      .map((n) => {
        const h = n.highlight as KGNode;
        const fig = kg.ref(n, "figures");
        const out: FeaturedPublication = { title: str(n.title)! };
        const img = str(fig?.content_url);
        if (img) out.image = img;
        const summary = str(h.summary);
        if (summary) out.description = summary;
        out.authors = many<KGNode>(n.authorships)
          .slice()
          .sort((a, b) => (num(a.position) ?? 0) - (num(b.position) ?? 0))
          .map((a) => str(a.author_name)!)
          .join(", ");
        out.link = { url: str(n.url), display: str(h.citation_text) };
        out.highlight = 1;
        const notes = many<unknown>(h.notes).map((x) => str(x)!);
        if (notes[0]) out.news2 = notes[0];
        return out;
      });
  };

  const news = (): NewsItem[] =>
    kg
      .ofType(T.NewsItem)
      .map((n) => {
        const d = str(n.date_published)!;
        const shown = str(n.period_text) ?? d.split("-").join(" ");
        return { date: shown, headline: str(n.headline)! };
      });


  function publicationsPage(): PublicationsPage {
    const page = kg.ofType(T.Page).find((p) => p.path === "/publications/");
    const topics = kg.refs(page, "featured_topics").map((t) => {
      const area: TopicArea = { label: str(t.pref_label)!, tag: str(t.notation)! };
      const def = str(t.definition);
      if (def) area.description = def;
      return area;
    });
    return {
      summary: str(page?.summary),
      keywords: many<unknown>(page?.keywords).map((k) => str(k)!),
      topics,
    };
  }

  return {
    teamMembers,
    students,
    alumniMembers,
    collaborators,
    projects,
    publications,
    publist,
    news,
    publicationsPage,
  };
}
