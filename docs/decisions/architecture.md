# Architecture decisions

Project-wide decisions about code structure, configuration and the application's design.

Entry format and rules: [README.md](README.md).

<!-- Log this project's decisions here, newest last, starting at D1. -->

---

# Examples

> [!NOTE]
> **Examples from the template, not decisions of this project.** They record why the
> [perception-template](https://github.com/REVEL-Robotics/perception-template) is set up the way it
> is. Delete this *Examples* section when you start a project from the template; if your project
> keeps or changes one of these choices, log it above as your own decision.

## D1: Vertical-slice code structure

- **Date:** 2026-10-15
- **Status:** Accepted
- **Context:** Layered layouts (`models/`, `utils/`, `services/`) spread one feature over many
  folders and couple features through shared layers.
- **Decision:** Group code by feature under `src/<package>/<feature>/`. Shared code goes to
  `src/<package>/shared/`; features never import from each other. Files stay under ~500 lines
  (single responsibility). Unit tests mirror `src/<package>/` under `tests/unit/`.
- **Consequences:** A feature can be understood, changed or deleted in one place. Some code may be
  duplicated across features until it is deliberately moved to `shared/`.

## D2: Single `config.yaml` with typed sections

- **Date:** 2026-10-15
- **Status:** Accepted
- **Context:** Settings scattered over constants, env variables and CLI flags are hard to find.
- **Decision:** All settings live in `config.yaml` in the repository root, one top-level section per
  feature plus `app`. Each feature parses its section into a frozen dataclass that validates
  values and rejects unknown keys. The path can be overridden with `--config`.
- **Consequences:** One place to look for settings; typos fail loudly at startup. Only PyYAML is
  needed; switch to pydantic if configs grow complex.

## D3: Plain Python, no ROS in the template

- **Date:** 2026-10-15
- **Status:** Accepted
- **Context:** Not every perception project needs ROS 2, and ROS adds a large dependency tree.
- **Decision:** The template is plain Python. Projects that need ROS 2 add it themselves (e.g. a
  RoboStack pixi environment) and log the decision.
- **Consequences:** Minimal template; ROS projects need extra setup.
