# CLAUDE.md

Python project managed with pixi. See README.md for the full structure.

## Commands

- `pixi run check`: lint, format check, typecheck and all tests. Run it before you finish a task.
- `pixi run format`: format and auto-fix lint issues.
- `pixi run test-unit` / `pixi run test-integration`: one test suite.
- `pixi add <pkg>` / `pixi add --pypi <pkg>`: add a dependency. Never use `pip install`, and never
  edit `pixi.lock` by hand.
- `docker build -f docker/Dockerfile -t <name> .`: build the image (from the repository root).

## Structure

- `src/<package>/<feature>/`: one folder per feature (vertical-slice architecture). A feature owns
  its config, logic and models, and exposes its public API in `__init__.py`.
- `src/<package>/shared/`: code used by more than one feature. Features never import from each other.
- `tests/unit/` mirrors `src/<package>/`: `src/<package>/a/b.py` → `tests/unit/a/test_b.py`.
- `tests/integration/`: run the whole application from a given input.
- `docker/`: `Dockerfile` and its `Dockerfile.dockerignore`; the build context is the repository root.
- `config.yaml`: all settings, one top-level section per feature (plus `app`). Add new settings
  here, read them through a typed dataclass in the feature's `config.py`; never hardcode them.

## Rules

- Never edit `.template.yaml`: it records the perception-template version this repository was
  created from. (In the perception-template repository itself, every PR bumps `template_version`;
  see README > Template versioning.)
- System dependencies live in `pixi.toml`: system libraries and tools are conda-forge dependencies
  (never `apt`/`brew` install steps, in docs or in the Dockerfile), and minimum kernel, glibc, macOS
  or CUDA driver versions go on the `[workspace] platforms` entries.
- Keep each file to a single responsibility and under ~500 lines; split it when it grows.
- Every new or changed behaviour gets a unit test; changes to the app's workflow also get an
  integration test.
- Type-annotate all functions; code must pass `ty check` and `ruff check`.
- **Decision log:** before changing a feature, read its `DECISIONS.md`; before a project-wide
  change, read the matching `docs/decisions/<scope>.md`. When you and the user agree on an
  architectural or technological decision (a library, a structure, a data format, a trade-off),
  add an entry in the same change, in the narrowest place it applies: the feature's `DECISIONS.md`
  or a scope file in `docs/decisions/`. Format and rules: `docs/decisions/README.md`.
  Entries under an *Examples* heading are the template's own decisions: they are not binding for
  this project and do not count towards the numbering.
