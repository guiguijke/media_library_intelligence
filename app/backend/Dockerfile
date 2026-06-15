FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 1000 mli \
    && useradd -u 1000 -g mli -m -s /bin/bash mli

RUN mkdir -p /app/data && chown -R mli:mli /app/data

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/mli/.local/bin:$PATH

COPY --from=builder --chown=mli:mli /root/.local /home/mli/.local
COPY --chown=mli:mli . .

USER mli

CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info"]
