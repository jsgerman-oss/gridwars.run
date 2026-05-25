FROM python:3.11-slim-bookworm

ENV DJANGO_SETTINGS_MODULE=server.conf.settings \
    PYTHONUNBUFFERED=1 \
    PATH="/home/evennia/.local/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc git gosu libffi-dev \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/sh evennia

WORKDIR /app

RUN pip install --no-cache-dir evennia==6.0.0

COPY --chown=evennia:evennia . .

RUN <<'EOF'
cat > /usr/local/bin/docker-entrypoint.sh <<'SCRIPT'
#!/bin/sh
set -eu

mkdir -p /data /app/server

if [ -f /app/server/evennia.db3 ] && [ ! -L /app/server/evennia.db3 ] && [ ! -s /data/evennia.db3 ]; then
    cp /app/server/evennia.db3 /data/evennia.db3
fi

rm -f /app/server/evennia.db3
ln -s /data/evennia.db3 /app/server/evennia.db3
chown -R evennia:evennia /data /app/server

gosu evennia python -m django migrate --noinput
exec gosu evennia evennia start --log
SCRIPT
chmod +x /usr/local/bin/docker-entrypoint.sh
EOF

EXPOSE 4000 4001

ENTRYPOINT ["docker-entrypoint.sh"]
