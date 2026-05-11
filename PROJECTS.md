# Editing the projects list

The `/research/` page is generated from `src/data/projects.yml`. Anyone can open
a pull request adding a new project, updating contributors, fixing a link, or
moving a project to "former" — no Astro / Node knowledge required.

## Schema

Each entry is a YAML object with these fields. Only `slug`, `title`, and
`status` are required.

```yaml
- slug: bbqs                       # required; url-safe, unique
  title: BBQS — Brain Behavior …   # required; human-readable
  status: active                   # required; "active" or "former"
  description: >                   # one-paragraph summary
    Sentence one. Sentence two.
  funder: NIDA U24 DA064429        # optional; grant / award id
  image: /images/external/bbqs.png # optional; path under public/
  themes: [open-data, consortium]  # optional; tags for filtering
  links:                           # optional list of { label, url }
    - { label: Project website, url: https://brain-bbqs.org }
    - { label: GitHub, url: https://github.com/brain-bbqs }
  contributors:                    # optional; both lists are optional
    current: [Satrajit S Ghosh, Nader Nikbakht]
    former: [Daniel M. Low]
```

## Contributor names

Names should match an entry in `src/data/team_members.yml`, `students.yml`, or
`alumni_members.yml`. When a name matches, the contributor renders as a link
to that person's anchor on `/team/` (e.g. `/team/#satrajit-s-ghosh`).

If a name **doesn't** match the roster, it still renders as plain text — fine
for one-off external collaborators. Just be aware: typos in names produce
dead links visually, plain-text-only renders.

To check the canonical name of a current/former member, search the roster
files:

```
grep -E '^- name:' src/data/team_members.yml src/data/alumni_members.yml
```

If a person should be on the site but isn't in any roster file, add them to
the appropriate one *in the same PR*.

## Status

- `active` — current work. Shows under "Active projects" on `/research/`.
- `former` — completed or paused. Shows under "Past projects". A `*` is
  appended to former-contributor names so a reader can quickly tell who's
  still in the lab.

When moving a project to `former`, also move former-current contributors into
`contributors.former`.

## Themes

Free-form lowercase-hyphen tags. Examples currently in use:

```
behavioral-quantification, child-development, clinical, computer-vision,
connectomics, consortium, deep-learning, education, knowledge-graphs, llm,
machine-learning, mental-health, naturalistic-data, neuroimaging,
neurophysiology, nlp, open-data, parcellation, reproducibility, review,
software, speech, speech-biomarkers, training, workflows
```

Reuse tags when reasonable. New tags are fine.

## TODO markers

Lines tagged with `# TODO …` are explicit invitations to fix something:

- `# TODO confirm <person>'s full name` — a contributor's name needs matching to the canonical roster
- `# TODO add <X> URL` — a link or DOI to be added
- `# TODO expand description` — a one-liner that should grow into a paragraph
- `# TODO list collaborators` — external collaborators (not in roster files) to add as bullet comments

When you address a TODO, remove the marker.

## Workflow

1. Edit `src/data/projects.yml` on a branch.
2. (Optional) `npm install && npm run build` to verify the YAML parses and renders.
3. Open a PR. The PR-preview deploy will surface the rendered `/research/`
   page at `https://sensein.group/pr-preview/pr-N/research/` so reviewers can
   see the change live.

## Removing a project

Delete its entry. Detail pages migrated from the legacy site
(`/mumble_melody_project/`, `/vocallect/`, etc.) live as separate Astro files
under `src/pages/` and aren't removed when the project entry is deleted —
remove them in the same PR if the page should also go.
