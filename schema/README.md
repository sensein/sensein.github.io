# Knowledge-graph schema

[`sensein.yaml`](./sensein.yaml) is the [LinkML](https://linkml.io) schema for
the lab knowledge graph in [`../kg/`](../kg). The graph is the site's only data
source; see [`../kg/README.md`](../kg/README.md) for how to edit it.

## Shape

The tree root is `KnowledgeGraph` (`dcat:Dataset`). Its slots are the record
collections, one per file in `kg/`. Every record class inherits from the
abstract `Record`, which carries the identifier and the provenance slots
(`created`, `modified`, `derived_from`, `curated_by`, `curation_notes`).

| Class | Maps to | Notes |
|---|---|---|
| `Person` | `schema:Person`, `foaf:Person`, `prov:Agent` | ORCID as `vivo:orcidId`; online accounts as `foaf:OnlineAccount` |
| `Organization` | `schema:Organization`, `foaf:Organization` | Universities, institutes, funders, with `parent_organization` |
| `Membership` | `org:Membership` | Person × organization × role × time; the roster is built from these |
| `Collaboration` | `prov:Association` (close) | External collaborator, projects, dates |
| `Project` | `schema:ResearchProject`, `prov:Activity` (close) | Lab projects and community efforts; funded by `Grant`s |
| `Grant` | `frapo:Grant`, `schema:Grant` | Award number, funder, the lab's role |
| `Publication` | `schema:ScholarlyArticle`, `bibo:AcademicArticle` (close) | Ordered `Authorship`s, `PreprintVersion`s, figures, `Highlight` |
| `Image` | `schema:ImageObject`, `foaf:Image` | Portraits, figures and logos: caption, alt text, credit, size, `foaf:depicts` |
| `Topic`, `TopicScheme` | `skos:Concept`, `skos:ConceptScheme` | The research-area vocabulary, with `broader` and `close_match` |
| `NewsItem` | `schema:NewsArticle` | `about` links to the people, projects or papers it concerns |
| `WebPageContent` | `schema:WebPage` | Page copy that is data |
| `BuildActivity`, `SourceFile` | `prov:Activity`, `prov:Entity` | Written by the build, not by hand |

Enums bind each value to an ontology term with `meaning:` where a good one
exists (publication types to FaBiO, project status to schema.org action
statuses). Dates use the `PartialDate` type (`YYYY`, `YYYY-MM` or
`YYYY-MM-DD`), which compiles to `xsd:gYear`, `xsd:gYearMonth` or `xsd:date`.

## Validate

```bash
pip install linkml -r requirements-kg.txt
python scripts/kg/build.py            # writes build/kg/sensein.yaml and the RDF
linkml-validate -s schema/sensein.yaml -C KnowledgeGraph build/kg/sensein.yaml
```

`scripts/kg/build.py --check` runs a faster built-in check (required slots,
enums, patterns, and that every reference resolves to a record of the right
class) and needs only PyYAML. CI runs both on any change to `kg/`, `schema/` or
`scripts/kg/` (see `.github/workflows/validate-data.yml`).

## Changing the schema

Bump `version` for any change that alters the RDF. New slots should reuse an
existing ontology property through `slot_uri` before minting a `sensein:` one,
and new classes should name their closest external class in `class_uri` or
`exact_mappings`. The JSON-LD context in `public/kg/context.jsonld` is generated
from the schema on every build, so it never needs editing by hand.
