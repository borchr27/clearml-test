# perception-template

Repository template for the Perception team: [pixi](https://pixi.prefix.dev/latest/) project with a
vertical-slice code layout, a single `config.yaml`, [Ruff](https://docs.astral.sh/ruff/) linting and
formatting, [ty](https://docs.astral.sh/ty/) typechecking, Docker packaging and GitHub Actions CI.

> **Using this template:** click *Use this template* on GitHub, then follow
> [Starting a new project](#starting-a-new-project) and replace this README with the
> [README layout](#readme-layout) below.

## Project structure

```
.
├── src/perception_template/      # source code, grouped by feature (vertical slices)
│   ├── __main__.py               # entry point: parses args, loads config, wires features together
│   ├── brightness_check/         # example feature: everything the feature needs lives here
│   │   ├── __init__.py           #   public API of the feature
│   │   ├── config.py             #   the feature's section of config.yaml
│   │   ├── check.py              #   the feature's logic
│   │   └── DECISIONS.md          #   decisions that only affect this feature
│   └── shared/                   # functionality used by several features (config, I/O, logging)
├── tests/
│   ├── unit/                     # unit tests, mirroring src/perception_template/ file by file
│   └── integration/              # runs the whole application from a given input
├── docs/
│   └── decisions/                # project-wide decision log, one file per scope
│       ├── README.md             #   where to log what, rules and entry format
│       └── architecture.md, tooling.md, deployment.md, workflow.md
├── config.yaml                   # application config, one section per feature
├── pixi.toml                     # pixi workspace: dependencies, system requirements, tasks, envs
├── pyproject.toml                # tool config only: ruff, ty, pytest
├── pixi.lock                     # locked dependencies, committed
├── docker/                       # container build of the pixi `prod` environment
│   ├── Dockerfile
│   └── Dockerfile.dockerignore   #   build-context allow-list for docker/Dockerfile
├── .github/workflows/
│   ├── ci.yml                    # lint, format, typecheck, tests and Docker build on every PR
│   └── template-version.yml      # template only: version bump check, tag and release
├── .template.yaml                # template version a project was created from
├── CLAUDE.md                     # instructions for Claude Code (structure and workflows)
└── .gitattributes / .gitignore
```

### Code structure rules

- **Vertical slices:** code is grouped by feature, not by technical layer. A feature folder holds
  its own config, logic and models, and exposes its public API in `__init__.py`.
- **Features do not import from each other.** Code needed by several features goes to `shared/`.
- **Single responsibility:** keep each file focused and under ~500 lines; split it when it grows.
- **System dependencies:** everything the project needs from the system is declared in
  `pixi.toml`. Libraries and tools come from conda-forge (`pixi add <package>`), not from apt or
  brew, and the minimum kernel, glibc, macOS and CUDA driver versions are declared per platform in
  `[workspace] platforms`.
- **Config:** every setting lives in `config.yaml`. Each feature reads its own top-level section
  into a typed dataclass (see `brightness_check/config.py`); `app` holds application-wide settings.
- **Tests:** `tests/unit/<path>/test_<module>.py` tests `src/perception_template/<path>/<module>.py`.
- **Decisions:** architectural and technological decisions are logged where they apply:
  project-wide ones in [docs/decisions/](docs/decisions/README.md), one file per scope, and
  feature-only ones in the feature's `DECISIONS.md`.

## Starting a new project

1. Rename the package: `src/perception_template/` → `src/<your_package>/`, update the imports,
   and `name` and `description` in `pixi.toml`.
2. Replace the example `brightness_check` feature (code, tests and its section in `config.yaml`)
   with your own features.
3. Add dependencies with `pixi add <package>` (conda-forge) or `pixi add --pypi <package>`.
4. Delete the *Examples* sections in `docs/decisions/*.md` (the template's own decisions) and log
   your project's decisions there, starting at D1 in each file.
5. Delete `.github/workflows/template-version.yml`, and keep `.template.yaml` unchanged: it
   records the template version the project was created from (see
   [Template versioning](#template-versioning)).

## Template versioning

`.template.yaml` holds the template version (`template_version`, `MAJOR.MINOR.PATCH`). It is
copied into every project created from the template, so each project records which template
structure it started from.

- Every PR to this template bumps `template_version`; the *Template version* workflow fails
  otherwise.
  - **MAJOR:** changes existing projects would have to adapt to (structure, config format, tasks).
  - **MINOR:** additions (a task, a shared helper, a CI job, a docs section).
  - **PATCH:** fixes and wording.
- On every merge to `main`, CI tags the commit `v<template_version>` and publishes a
  [GitHub release](https://github.com/REVEL-Robotics/perception-template/releases) with the merged
  PRs as notes. Every commit on `main` is therefore a release, and a version is exactly one commit.
  This relies on `main` being changed only through PRs (branch protection).
- From a project, the template it was created from is
  `https://github.com/REVEL-Robotics/perception-template/tree/v<version>`, and the template changes
  since then are `https://github.com/REVEL-Robotics/perception-template/compare/v<version>...main`.

## Development

Requires [pixi](https://pixi.prefix.dev/latest/installation/) 0.82 or newer (`pixi self-update`)
and Docker for the container build. Python (3.14) and all other dependencies are installed by pixi.

```bash
pixi install                    # create the environment from pixi.lock
pixi run start <image.npy>      # run the app (reads config.yaml; --config <path> to override)
pixi run check                  # lint + format check + typecheck + all tests (what CI runs)
pixi run format                 # format and auto-fix
pixi task list                  # all tasks
```

Docker:

```bash
docker build -f docker/Dockerfile -t perception-template .   # from the repository root
docker run --rm -v "$PWD/data:/data" perception-template /data/image.npy
```

---

## README layout

Copy this layout over the content above when you start a project, and fill in each section.

````markdown
# <project-name>

<One or two sentences: what the project does and for whom.>

Created from [perception-template v<version>](https://github.com/REVEL-Robotics/perception-template/tree/v<version>)
(see `.template.yaml`).

## Overview

<The problem it solves, the inputs it takes and the outputs it produces. A diagram if helpful.>

## Features

| Feature | Folder | Description |
| ------- | ------ | ----------- |
| <name>  | `src/<package>/<feature>/` | <what it does> |

## Project structure

```
.
├── src/<package>/
│   ├── __main__.py               # entry point: parses args, loads config, wires features together
│   ├── <feature>/                # one folder per feature (vertical slice)
│   │   ├── __init__.py           #   public API of the feature
│   │   ├── config.py             #   the feature's section of config.yaml
│   │   ├── <module>.py           #   the feature's logic
│   │   └── DECISIONS.md          #   decisions that only affect this feature
│   └── shared/                   # functionality used by several features
├── tests/
│   ├── unit/                     # unit tests, mirroring src/<package>/ file by file
│   └── integration/              # runs the whole application from a given input
├── docs/
│   └── decisions/                # project-wide decision log, one file per scope
├── config.yaml                   # application config, one section per feature
├── pixi.toml / pixi.lock         # dependencies, tasks, environments / locked dependencies
├── pyproject.toml                # tool config only: ruff, ty, pytest
├── docker/                       # Dockerfile and Dockerfile.dockerignore
├── .github/workflows/ci.yml
├── .template.yaml                # perception-template version this repo was created from
└── CLAUDE.md
```

<Add project-specific folders (e.g. data, models, scripts) and what they contain.>

- Code is grouped by feature; features do not import from each other, shared code goes to `shared/`.
- Every setting lives in `config.yaml`, in the section of the feature that uses it.
- `tests/unit/<path>/test_<module>.py` tests `src/<package>/<path>/<module>.py`.

## Getting started

### Prerequisites

<Hardware (GPU, cameras, robot), OS, and tools: pixi, Docker. Software dependencies, including the
minimum glibc, macOS and CUDA driver versions, are in `pixi.toml`.>

### Installation

```bash
pixi install
```

### Usage

```bash
pixi run start <args>
```

<Example input and expected output.>

## Configuration

<The sections of config.yaml and what the important keys do.>

## Development

```bash
pixi run check     # lint, format check, typecheck, tests
pixi run format    # format and auto-fix
```

## Deployment

<How the Docker image (`docker/Dockerfile`) is built, run and where it is deployed.>

## Decisions

Project-wide decisions are in [docs/decisions/](docs/decisions/README.md), grouped by scope;
decisions that only affect one feature are in `src/<package>/<feature>/DECISIONS.md`.
````
