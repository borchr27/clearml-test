# Workflow decisions

Project-wide decisions about how the team works on the repository: documentation, versioning, reviews and releases.

Entry format and rules: [README.md](README.md).

<!-- Log this project's decisions here, newest last, starting at D1. -->

---

# Examples

> [!NOTE]
> **Examples from the template, not decisions of this project.** They record why the
> [perception-template](https://github.com/REVEL-Robotics/perception-template) is set up the way it
> is. Delete this *Examples* section when you start a project from the template; if your project
> keeps or changes one of these choices, log it above as your own decision.

## D1: Template versioning with a version file and git tags

- **Date:** 2026-10-16
- **Status:** Accepted
- **Context:** Projects created from the template should record which template commit they
  started from, so the template-driven structure is versioned and traceable in each project.
  GitHub's *Use this template* creates a repository with a fresh history, and a file cannot contain
  the hash of the commit it is part of.
- **Decision:** `.template.yaml` holds a semver `template_version` and is copied into every project.
  Every template PR must bump it (checked in CI), and every merge to `main` is tagged
  `v<template_version>` with a GitHub release, so a version maps to exactly one commit. Projects
  keep using the *Use this template* button.
- **Consequences:** No extra tooling for creating projects. A version, not a raw SHA, is recorded;
  the tag resolves it. There is no automatic way to pull template updates into existing projects;
  they compare `v<version>...main` and port changes by hand. Considered: Copier (records the
  commit and supports `copier update`, but needs Jinja-templated files and a CLI instead of the
  button) and a first-push workflow writing the SHA (needs an org token, because the template is
  private).

## D2: Decision log grouped by scope and feature

- **Date:** 2026-10-16
- **Status:** Accepted
- **Context:** A single decision log grows linearly with the project's lifetime, and reading it
  to find the decisions relevant to one change gets slower for people and for AI assistants.
- **Decision:** Project-wide decisions live in `docs/decisions/<scope>.md` (architecture, tooling,
  deployment, workflow; add scopes as needed). Decisions that only affect one feature live in
  `src/<package>/<feature>/DECISIONS.md`, next to the code. Entries are numbered per file and
  referenced as `<scope>/D<n>` or `<feature>/D<n>`.
- **Consequences:** Each file stays short and is read only when its scope or feature is touched; a
  feature's decisions are moved or deleted together with its code. Deciding the right scope takes
  a moment; a feature decision that later affects several features is superseded by a project-wide
  one. Considered: one file per decision with a generated index (more files and tooling) and
  a short summary of current decisions (a second place to keep up to date).
