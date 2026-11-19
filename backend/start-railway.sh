#!/bin/sh
set -eu
: "${RAILWAY_VOLUME_MOUNT_PATH:?Attach a writable Railway volume to this service}"
if [ ! -d "$RAILWAY_VOLUME_MOUNT_PATH" ] || [ ! -w "$RAILWAY_VOLUME_MOUNT_PATH" ]; then
    echo "The Railway upload volume is not mounted or writable." >&2
    exit 1
fi
python manage.py migrate --noinput
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers "${WEB_CONCURRENCY:-2}"
