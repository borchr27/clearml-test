# Decisions

Architectural and technological decisions of this project. Every decision agreed with an AI
assistant is logged too. Decisions are grouped by where they apply, so each file stays short and
only the relevant ones need to be read.

| Where | What goes there |
| ----- | --------------- |
| [architecture.md](architecture.md) | Code structure, configuration, application design |
| [tooling.md](tooling.md) | Dependency management, development tools, CI checks |
| [deployment.md](deployment.md) | Packaging, containers, where the application runs |
| [workflow.md](workflow.md) | How the team works: documentation, versioning, reviews, releases |
| `src/<package>/<feature>/DECISIONS.md` | Decisions that only affect that feature |
| `src/<package>/shared/DECISIONS.md` | Decisions about the shared code |

Add a scope file here when a new project-wide area appears (e.g. `data.md`, `hardware.md`,
`models.md`), and list it in the table. Create a feature's `DECISIONS.md` with its first decision.

## Rules

- Log a decision in the narrowest place it applies: a feature's `DECISIONS.md` if only that feature
  is affected, otherwise the matching scope file here.
- Entries are numbered per file, newest last, and referenced as `<scope>/D<n>` (e.g.
  `tooling/D2`) or `<feature>/D<n>` (e.g. `brightness_check/D1`).
- Do not rewrite old entries. When a decision changes, add a new entry and set the old one's status
  to `Superseded by <scope>/D<n>`. When a feature decision starts to affect several features, log
  it in a scope file and supersede the feature entry.
- A feature's decisions are moved or deleted together with the feature.

## Entry format

```markdown
## D<n>: <Short title>

- **Date:** YYYY-MM-DD
- **Status:** Accepted | Superseded by <scope>/D<n>
- **Context:** <The problem or the forces at play.>
- **Decision:** <What was decided.>
- **Consequences:** <What it makes easier or harder; alternatives considered.>
```
