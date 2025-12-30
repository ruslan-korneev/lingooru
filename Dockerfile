FROM python:3.13.5-slim-bullseye

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential=12.9 \
      libffi-dev=3.3-6 \
      curl \
 && rm -rf /var/lib/apt/lists/*


COPY --from=ghcr.io/astral-sh/uv:0.9.2 /uv /uvx /bin/

COPY . /app
WORKDIR /app

RUN uv sync --frozen

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

ENTRYPOINT ["scripts/entrypoint.sh"]
