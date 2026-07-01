# Data schema

[`sensein.yaml`](./sensein.yaml) is a [LinkML](https://linkml.io) schema for the
structured YAML that drives the site (everything in [`../src/data/`](../src/data)).
It exists so the data can be validated in CI and so the model is documented and
ontology-aligned.

## What it covers

| Data file | Target class |
|---|---|
| `team_members.yml`, `students.yml`, `alumni_members.yml` | `TeamMember` |
| `collaborators.yml` | `Collaborator` |
| `projects.yml` | `Project` (+ `ProjectLink`, `ProjectContributors`) |
| `publications.yml` | `Publication` (+ `PreprintRef`) |
| `publist.yml` | `FeaturedPublication` (+ `LinkDisplay`) |
| `news.yml` | `NewsItem` |
| `publications_page.yml` | `PublicationsPage` (+ `TopicArea`) |

## Design

- **PROV-DM typing.** Classes mix in one of three abstract PROV mixins so the
  data is provenance-typed: people (`TeamMember`, `Collaborator`) are
  `prov:Agent`, projects (`Project`) are `prov:Activity`, and everything else
  (publications, links, news, page content) is `prov:Entity`. Relational slots
  carry PROV predicates via `slot_uri` — e.g. `authors` → `prov:wasAttributedTo`,
  `preprints` → `prov:wasRevisionOf`, `sources` → `prov:wasDerivedFrom`,
  `publications`/`projects` → `prov:generated`/`prov:wasGeneratedBy`,
  `contributors` → `prov:qualifiedAssociation`.
- **SKOS ontology alignment.** Every class and slot is aligned to external
  vocabularies (schema.org, Dublin Core Terms, FOAF, FaBiO/SPAR, BIBO, PRISM,
  Wikidata) through SKOS mapping predicates — `exact_mappings`,
  `close_mappings`, and `related_mappings`.
- **Enum meanings.** Every permissible value in every enum (`ProjectStatus`,
  `PublicationType`, `PublicationCategory`, `AbstractSource`) carries a
  `meaning:` binding to an ontology term (e.g. `journal` → `fabio:JournalArticle`,
  `pubmed` → `wikidata:Q180686`).

## Validate locally

```bash
pip install linkml pyyaml
python schema/validate_data.py
```

The script validates every record in each data file against its target class
and exits non-zero on any error. CI runs the same check on changes to
`src/data/**` or `schema/**` (see `.github/workflows/validate-data.yml`).
