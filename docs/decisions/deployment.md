# Deployment decisions

Project-wide decisions about packaging, containers and where the application runs.

Entry format and rules: [README.md](README.md).

<!-- Log this project's decisions here, newest last, starting at D1. -->

---

# Examples

> [!NOTE]
> **Examples from the template, not decisions of this project.** They record why the
> [perception-template](https://github.com/REVEL-Robotics/perception-template) is set up the way it
> is. Delete this *Examples* section when you start a project from the template; if your project
> keeps or changes one of these choices, log it above as your own decision.

## D1: Docker image built from the pixi `prod` environment

- **Date:** 2026-10-15
- **Status:** Accepted
- **Context:** Deployments need a container identical to the locked environment, without dev tools.
- **Decision:** Multi-stage Dockerfile: install the `prod` pixi environment (no dev feature) with
  `--locked` in the official pixi image, then copy only the environment, source and config into
  `ubuntu:24.04`. The image is built (not pushed) in CI on every pull request.
- **Consequences:** Small runtime image with exactly the locked dependencies. Publishing the
  image to a registry is left to each project.

## D2: Docker files in `docker/`

- **Date:** 2026-10-20
- **Status:** Accepted
- **Context:** Container files in the repository root mix with project files, and projects often add
  more of them (compose files, entrypoint scripts, further Dockerfiles).
- **Decision:** Docker files live in `docker/`: `docker/Dockerfile` and its build-context allow-list
  `docker/Dockerfile.dockerignore` (BuildKit reads `<Dockerfile>.dockerignore` next to the
  Dockerfile). The build context stays the repository root:
  `docker build -f docker/Dockerfile -t <name> .`.
- **Consequences:** A tidier root and one place for container files. Builds need `-f
  docker/Dockerfile`, and the ignore file is only honoured by BuildKit (the default builder).
