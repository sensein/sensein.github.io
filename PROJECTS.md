# Editing the projects list

The `/research/` page is generated from the lab knowledge graph. Projects live
in [`kg/projects.yaml`](kg/projects.yaml), their awards in
[`kg/grants.yaml`](kg/grants.yaml), and the papers they cite in
[`kg/publications.yaml`](kg/publications.yaml). Anyone can open a pull request
adding a project, updating its members, fixing a link or marking it former; no
Astro or Node knowledge is needed. [`kg/README.md`](kg/README.md) covers the
graph as a whole.

## A project record

Only `id`, `slug`, `title` and `project_type` are required.

```yaml
- id: sid:project/bbqs              # required; sid:project/<slug>
  slug: bbqs                        # required; url-safe, unique
  title: BBQS — Brain Behavior …    # required
  project_type: lab_project         # required; or community_effort
  project_status: active            # active or former
  start_date: '2024'                # optional; YYYY, YYYY-MM or YYYY-MM-DD
  description: >-
    Sentence one. Sentence two.
  funding_statement: NIDA U24 DA064429 (Lead PI; MPI Cabrera, Kennedy)
  funded_by:                        # grant ids from kg/grants.yaml
  - sid:grant/u24-da064429
  image: sid:image/external/bbqs-logo   # an id from kg/images.yaml
  themes:                           # topic ids from kg/topics.yaml
  - sid:topic/open-data-standards
  links:
  - url: https://brain-bbqs.org
    label: Project website
  members:                          # person ids
  - sid:person/satrajit-s-ghosh
  former_members:
  - sid:person/daniel-m-low
  external_contributors:            # free text for people with no record
  - Rachel Reetzke (Kennedy Krieger)
  anchor_publications:              # publication ids, usually DOI:…
  - DOI:10.1234/example
  created: '2026-12-01'
```

The build stops with a clear message if any id here points at nothing, so a
typo in a name can't produce a silent dead link.

### Linking publications

List the paper's id under `anchor_publications`. If the paper isn't in
`kg/publications.yaml` yet, add it in the same PR, and set its own `projects:`
to include this project so the link works both ways.

## People

Members are referenced by id. To find someone's id:

```
grep -n "^- id: sid:person/" kg/people.yaml
```

If a contributor is in the lab but has no record, add them to
`kg/people.yaml` (and a membership to `kg/memberships.yaml`) in the same PR.
Someone outside the lab can go under `external_contributors` as text, or get a
person record if they will appear elsewhere on the site.

## Status

- `active`: current work. Shows under "Active projects" on `/research/`.
- `former`: completed or paused. Shows under "Past projects". Set `end_date`
  too.

When a project ends, move people who are no longer on it from `members` to
`former_members`.

## Themes

Themes are topics from the research-area vocabulary in
[`kg/topics.yaml`](kg/topics.yaml): `skos:Concept`s with a label and a
definition. Reuse one where it fits. A new theme needs a new topic record in
the same PR.

## Open questions

Anything a project record still needs (a missing link, an unconfirmed name, a
description to expand) is listed under its `curation_notes`. When you resolve
one, remove the note.

## Workflow

1. Edit `kg/projects.yaml` on a branch.
2. (Optional) `pip install -r requirements-kg.txt && npm run kg` to check the
   graph, or `npm install && npm run build` to render the site.
3. Open a PR. The PR-preview deploy will surface the rendered `/research/`
   page at `https://sensein.group/pr-preview/pr-N/research/` so reviewers can
   see the change live.

## Removing a project

Delete its entry. Detail pages migrated from the legacy site
(`/mumble_melody_project/`, `/vocallect/`, etc.) live as separate Astro files
under `src/pages/` and aren't removed when the project entry is deleted —
remove them in the same PR if the page should also go.
