# The lab knowledge graph

Everything the website says about the lab — people, roles, projects, grants,
publications, figures, news and page copy — lives in this folder as one
knowledge graph. The site is built from it, and nothing else. To change what
the site shows, change the graph.

The graph is described by the LinkML schema in
[`../schema/sensein.yaml`](../schema/sensein.yaml), which reuses schema.org,
FOAF, W3C ORG, PROV-O, Dublin Core, DCAT, SKOS, FaBiO/FRAPO (SPAR), BIBO and
VIVO terms, so the compiled graph is ordinary linked data that BrainKB or any
RDF store can load.

## Layout

Each file holds one kind of record. Together they form a single
`KnowledgeGraph`; the split is only for readability.

| File | Holds | RDF type |
|---|---|---|
| `people.yaml` | Lab members, alumni and external collaborators | `schema:Person` |
| `memberships.yaml` | Each person's role in the lab, with dates | `org:Membership` |
| `collaborations.yaml` | External collaborators and the projects they work on | `sensein:Collaboration` |
| `organizations.yaml` | Universities, institutes and funders | `schema:Organization` |
| `projects.yaml` | Lab projects and the community efforts the lab takes part in | `schema:ResearchProject` |
| `grants.yaml` | Awards that fund projects | `frapo:Grant` |
| `publications.yaml` | Papers, preprints and talks, with authorship order and figures | `schema:ScholarlyArticle` |
| `images.yaml` | Every portrait, project image, figure and logo the site serves | `schema:ImageObject` |
| `topics.yaml` | The research-area vocabulary | `skos:ConceptScheme`, `skos:Concept` |
| `news.yaml` | Dated announcements | `schema:NewsArticle` |
| `pages.yaml` | Page copy that is data rather than layout (e.g. the publications intro) | `schema:WebPage` |

## Identifiers

Every record has a stable IRI, written as a CURIE:

- `sid:` expands to `https://sensein.group/id/`, so `sid:person/satrajit-s-ghosh`
  is `https://sensein.group/id/person/satrajit-s-ghosh`.
- Publications use their DOI where they have one (`DOI:10.1162/imag.a.1116`),
  then arXiv (`arXiv:`), then PubMed (`PMID:`), then `sid:publication/<slug>`.
- People carry their ORCID (`orcid: ORCID:0000-…`) when known.

References between records are by id: a membership's `member` is a person id,
a project's `funded_by` lists grant ids, an image's `depicts` lists the people
or projects in it. The build fails if a reference points at nothing, or at a
record of the wrong kind.

## Provenance and time

- **`created`** is the date the record first appeared in the site's history
  (taken from git when the graph was migrated; set it to today when you add
  one).
- **`modified`** is not stored. The build works it out from `git blame` on the
  record's lines, so it is always right.
- **`derived_from`** says where the facts came from: `pubmed`, `ncbi`,
  `openalex`, `crossref`, `cv`, `site-yaml-v1` (the pre-graph site data), and so
  on.
- **`curated_by`** and **`curation_notes`** record who checked a record and
  anything still unresolved.
- Roles, collaborations, projects and grants carry **`start_date`** and
  **`end_date`** as `YYYY`, `YYYY-MM` or `YYYY-MM-DD`. A membership with no
  `end_date` and `membership_status: current` is a current role. `period_text`
  keeps the wording the site displays ("Fall 2020 – 2023") when it says more than the
  dates do.
- Every build also writes a `prov:Activity` describing itself: when it ran, the
  commit it built, and the checksum and last commit of every file here. That
  node sits at the top of the compiled graph.

## Common edits

**A new lab member.** Add a person to `people.yaml`, a membership to
`memberships.yaml`, and (if there is a photo) the file under
`public/images/people/` plus an image record in `images.yaml`:

```yaml
# people.yaml
- id: sid:person/ada-lovelace
  name: Ada Lovelace
  slug: ada-lovelace
  orcid: ORCID:0000-0000-0000-0000
  email: ada@mit.edu
  image: sid:image/people/ada-lovelace
  accounts:
  - service: github
    account_name: ada
    url: https://github.com/ada
  education:
  - statement: PhD Mathematics, University of London
  created: '2026-12-01'

# memberships.yaml
- id: sid:membership/ada-lovelace
  member: sid:person/ada-lovelace
  organization: sid:org/sensein
  membership_status: current
  role_title: Postdoctoral Associate
  role_category: postdoc
  start_date: '2026-12'
  roster_section: members   # or students
  roster_order: 20          # position on the team page
  created: '2026-12-01'

# images.yaml
- id: sid:image/people/ada-lovelace
  content_url: /images/people/ada-lovelace.webp
  image_kind: portrait
  encoding_format: image/webp
  width: 320
  height: 320
  depicts:
  - sid:person/ada-lovelace
```

**Someone leaves.** On their membership, set `membership_status: former`, add
an `end_date`, and optionally a `period_text`. Don't delete the person.

**A new paper.** Add it to `publications.yaml` with its DOI as the id, the
author list in order under `authorships` (link lab members with `agent:`), the
projects and topics it belongs to, and `derived_from` for where you got the
metadata. A figure for the highlights list goes in `images.yaml` with
`image_kind: figure`, a caption and `alt_text`, and is linked from the paper's
`figures`.

**A new project.** Add it to `projects.yaml` with `project_type: lab_project`,
its members, links and themes. Put the award in `grants.yaml` and link it with
`funded_by`; keep the human-readable `funding_statement` too.

## Building and checking

```bash
pip install -r requirements-kg.txt
npm run kg                      # same as: python3 scripts/kg/build.py
python3 scripts/kg/build.py --check   # validate only
```

The build checks every record against the schema, then writes:

- `public/kg/sensein.jsonld` — the graph as JSON-LD 1.1, served at
  `https://sensein.group/kg/sensein.jsonld`
- `public/kg/sensein.ttl` — the same graph as Turtle
- `public/kg/context.jsonld` — the JSON-LD context, generated from the schema
- `src/generated/sensein.jsonld` — the copy the site reads at build time
- `build/kg/sensein.yaml` — the merged graph, for `linkml-validate`

`npm run dev` and `npm run build` run it first, so you rarely need to call it
yourself. CI also runs the full LinkML validator on every pull request that
touches this folder.

## What the pages take from the graph

- **Grants.** `grants.yaml` follows the grant list in Satra's CV, current and
  past, with titles, years, funder, the lab's role and co-investigators, but no
  amounts. `award_status` (current or past) follows the CV's headings. The
  research page's Funding section lists every grant with the projects it funds.
  A project page lists each award from `funded_by` with its funder, award
  number, role and years; cards and publication pages show the short form
  ("NIDA U24 DA064429"). A project page also shows `funding_statement` when it
  says more than the project's one grant, or when the project has no grant.
- **Images and figures.** Pages set each image's `width` and `height` from its
  record, so the layout doesn't jump as images load. `alt_text` and `caption`
  are used wherever they are filled in; until then the page falls back to the
  project or paper title. A paper's `figures` appear on its own page.
- **Linked data on every page.** Each project and publication page embeds its
  record, and the records it points to, as JSON-LD in the page head, using the
  published context. Every page also links to the full graph as JSON-LD and
  Turtle.

## Loading into BrainKB

The site reads only the compiled JSON-LD, through `src/lib/kg.ts` and
`src/lib/extract.ts`, and any JSON-LD document compacted with
`public/kg/context.jsonld` can stand in for it. So the graph can be ingested
into BrainKB as `sensein.ttl`, and the site can later be built from a BrainKB
export instead of these files, statically or at request time, without changing
the pages.
