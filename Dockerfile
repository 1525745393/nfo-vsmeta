FROM python:3.11-slim

LABEL maintainer="NFO to VSMETA Team"
LABEL description="NFO to VSMETA Converter - Convert Kodi NFO files to Synology Video Station VSMETA format"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY server ./server
COPY ui ./ui
COPY config ./config
COPY plugins ./plugins

RUN pip install --no-cache-dir -e ".[all]"

ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

ENTRYPOINT ["nfo-vsmeta-web"]
