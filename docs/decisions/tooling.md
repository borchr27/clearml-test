# Tooling decisions

Project-wide decisions about dependency management, development tools and CI checks.

Entry format and rules: [README.md](README.md).

<!-- Log this project's decisions here, newest last, starting at D1. -->

---

# Examples

> [!NOTE]
> **Examples from the template, not decisions of this project.** They record why the
> [perception-template](https://github.com/REVEL-Robotics/perception-template) is set up the way it
> is. Delete this *Examples* section when you start a project from the template; if your project
> keeps or changes one of these choices, log it above as your own decision.

## D1: Pixi for project and dependency management

- **Date:** 2026-10-15
- **Status:** Accepted
- **Context:** Perception projects need both conda packages (CUDA, OpenCV, native libraries) and
  PyPI packages, reproducible across developer machines, CI and Docker.
- **Decision:** Use pixi with conda-forge, with the manifest in `pixi.toml` (as in the team's other
  repositories). The code in `src/` is not installed as a package but made importable with
  `PYTHONPATH=$PIXI_PROJECT_ROOT/src` (`[activation.env]`). The ruff, ty and pytest configs live
  in `pyproject.toml`, which holds only `[tool.*]` tables (no `[project]`), so there is one file
  for tool config instead of three. `pixi.lock` is committed. Tasks (`pixi run ...`) are the
  single entry point for running, testing and checking.
- **Consequences:** One tool replaces conda/venv/pip/Makefiles. Contributors need pixi installed.
  The app runs as `python -m <package>` (no console script); if the project must be published as
  a Python package, add a `[project]` table to `pyproject.toml` and log the decision.

## D2: Ruff and ty for code quality

- **Date:** 2026-10-15
- **Status:** Accepted
- **Context:** Need fast, consistent linting, formatting and typechecking locally and in CI.
- **Decision:** Ruff for linting and formatting (line length 100), ty for typechecking. Both run in
  CI on every pull request.
- **Consequences:** Single fast toolchain from Astral. ty is pre-1.0, so occasional false positives
  or rule changes are possible.

## D3: System dependencies declared in `pixi.toml`

- **Date:** 2026-10-20
- **Status:** Accepted
- **Context:** Perception projects depend on system libraries (OpenCV backends, camera SDKs, CUDA)
  and on host versions (kernel, glibc, macOS, GPU driver). Installed by hand with apt or brew, or
  only listed in a README, they drift between developer machines, CI and Docker.
- **Decision:** `pixi.toml` is the single place for system dependencies. Libraries and tools are
  conda-forge dependencies, never apt or brew steps. The minimum host versions are declared as
  virtual packages on named `[workspace] platforms` entries (`linux`, `glibc`, `macos`, `cuda`),
  starting from pixi's defaults (Linux 4.18, glibc 2.28, macOS 13.0) and raised only when a
  dependency needs it. `requires-pixi = ">=0.82.0"` because older pixi versions cannot read these
  entries.
- **Consequences:** Host requirements are visible in the manifest and recorded in `pixi.lock`; pixi
  refuses to install on an older host instead of failing at runtime. Developers need pixi 0.82+.
  Platforms carry explicit names (`linux-x64`, …) because pixi rejects an unnamed entry that
  only restates its defaults. Considered: the `[system-requirements]` table (deprecated, prints a
  warning on every pixi command) and bare platform names (requirements stay implicit).

## D4: Python 3.14

- **Date:** 2026-10-20
- **Status:** Accepted
- **Context:** The template started on Python 3.12. New projects should start on the newest Python
  that conda-forge and the dependencies support, to avoid an early upgrade.
- **Decision:** `python = "3.14.*"` in `pixi.toml`; ruff (`target-version = "py314"`) and ty
  (`python-version = "3.14"`) check against the same version.
- **Consequences:** Projects get current language features and the longest support window. A
  dependency without 3.14 builds on conda-forge forces a downgrade, logged as a project decision.
