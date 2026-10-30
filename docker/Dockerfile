# Multi-stage build of the pixi project. Build from the repository root (the build context):
#   docker build -f docker/Dockerfile -t perception-template .
#   docker run --rm -v "$PWD/data:/data" perception-template /data/image.npy
#
# Stage 1 installs the `prod` pixi environment (no dev tools) from the lockfile.
# Stage 2 copies only that environment into a slim image; pixi itself is not shipped.
# Dockerfile.dockerignore (next to this file) limits the build context to what the image needs.

ARG PIXI_VERSION=0.82.0

FROM ghcr.io/prefix-dev/pixi:${PIXI_VERSION}-noble AS build

WORKDIR /app
COPY pixi.toml pixi.lock ./
RUN pixi install --locked --environment prod
# Activation script: puts the environment on PATH and sets the [activation.env] variables
# (PYTHONPATH=/app/src).
RUN pixi shell-hook --environment prod --shell bash > /shell-hook.sh \
    && echo 'exec "$@"' >> /shell-hook.sh

FROM ubuntu:24.04 AS production

WORKDIR /app
# Same path as in the build stage: the environment contains absolute paths.
COPY --from=build /app/.pixi/envs/prod /app/.pixi/envs/prod
COPY --from=build /shell-hook.sh /shell-hook.sh
COPY config.yaml ./
COPY src ./src

ENTRYPOINT ["/bin/bash", "/shell-hook.sh", "python", "-m", "perception_template"]
CMD ["--help"]
