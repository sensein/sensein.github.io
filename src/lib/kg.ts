/**
 * Read access to the lab knowledge graph.
 *
 * The site never reads the YAML sources in kg/. It reads the compiled
 * JSON-LD graph (src/generated/sensein.jsonld, written by
 * scripts/kg/build.py) through the small index below. Any JSON-LD document
 * compacted with public/kg/context.jsonld works as input, so a graph
 * exported from BrainKB can drive the same pages.
 *
 * This module only uses type syntax that Node can strip, so it can be
 * imported by plain Node scripts (scripts/kg/check-roundtrip.mjs) as well
 * as by Astro.
 */

export type Scalar = string | number | boolean;
export type ValueObject = { "@value": Scalar; "@type"?: string };
export interface KGNode {
  id?: string;
  type?: string[];
  [slot: string]: unknown;
}
export interface JsonLdDocument {
  "@context"?: unknown;
  "@graph": KGNode[];
}

/** Literal value of a slot, unwrapping JSON-LD value objects. */
export function lit(v: unknown): Scalar | undefined {
  if (v === null || v === undefined) return undefined;
  if (typeof v === "object" && v !== null && "@value" in (v as ValueObject)) {
    return (v as ValueObject)["@value"];
  }
  if (typeof v === "string" || typeof v === "number" || typeof v === "boolean") return v;
  return undefined;
}

export function str(v: unknown): string | undefined {
  const x = lit(v);
  return x === undefined ? undefined : String(x);
}

export function num(v: unknown): number | undefined {
  const x = lit(v);
  if (x === undefined) return undefined;
  const n = typeof x === "number" ? x : Number(x);
  return Number.isNaN(n) ? undefined : n;
}

export function many<T = unknown>(v: unknown): T[] {
  if (v === null || v === undefined) return [];
  return (Array.isArray(v) ? v : [v]) as T[];
}

export class KnowledgeGraph {
  readonly nodes: KGNode[];
  readonly byId: Map<string, KGNode>;
  readonly byType: Map<string, KGNode[]>;

  constructor(doc: JsonLdDocument) {
    this.nodes = doc["@graph"] ?? [];
    this.byId = new Map();
    this.byType = new Map();
    for (const n of this.nodes) {
      if (n.id) this.byId.set(n.id, n);
      for (const t of many<string>(n.type)) {
        const list = this.byType.get(t) ?? [];
        list.push(n);
        this.byType.set(t, list);
      }
    }
  }

  /** Nodes of an RDF type (CURIE as in the context, e.g. "schema:Person"),
   *  in the order the graph lists them. */
  ofType(type: string): KGNode[] {
    return this.byType.get(type) ?? [];
  }

  get(id: unknown): KGNode | undefined {
    return typeof id === "string" ? this.byId.get(id) : undefined;
  }

  /** Follow a reference slot to the node(s) it points at. */
  refs(node: KGNode | undefined, slot: string): KGNode[] {
    if (!node) return [];
    return many<string>(node[slot])
      .map((id) => this.byId.get(id))
      .filter((n): n is KGNode => Boolean(n));
  }

  ref(node: KGNode | undefined, slot: string): KGNode | undefined {
    return this.refs(node, slot)[0];
  }

  /** The graph's own description (id sid:graph/sensein). */
  dataset(): KGNode | undefined {
    return this.ofType("dcat:Dataset")[0];
  }
}

/** RDF types used by the site, as CURIEs from the schema's class_uri. */
export const T = {
  Person: "schema:Person",
  Organization: "schema:Organization",
  Membership: "org:Membership",
  Collaboration: "sensein:Collaboration",
  Project: "schema:ResearchProject",
  Grant: "frapo:Grant",
  Publication: "schema:ScholarlyArticle",
  Image: "schema:ImageObject",
  Topic: "skos:Concept",
  TopicScheme: "skos:ConceptScheme",
  NewsItem: "schema:NewsArticle",
  Page: "schema:WebPage",
} as const;
