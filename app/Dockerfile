# === Stage 1: Build Frontend ===
FROM node:24-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY frontend/ .
RUN npm run build

# === Stage 2: Python dependencies ===
FROM python:3.12-slim AS python-builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# === Stage 3: Final image ===
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 1000 mli \
    && useradd -u 1000 -g mli -m -s /bin/bash mli

RUN mkdir -p /app/data && chown -R mli:mli /app/data

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/mli/.local/bin:$PATH

COPY --from=python-builder --chown=mli:mli /root/.local /home/mli/.local
COPY --from=frontend-builder --chown=mli:mli /frontend/dist /app/static

COPY --chown=mli:mli backend/ .

USER mli

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:3000/api/health > /dev/null || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
