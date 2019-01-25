#!/bin/bash
set -e

until psql $DATABASE_URL -c '\l'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - continuing"

./bin/mapit_make_css
python manage.py collectstatic --clear --noinput  # Collect static files

python manage.py migrate --noinput                # Apply database migrations

# Prepare log files and start outputting logs to stdout
touch /src/logs/gunicorn.log
touch /src/logs/access.log
tail -n 0 -f /src/logs/*.log &

# Start Gunicorn processes
echo Starting Gunicorn.
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --worker-class gevent \
    --log-level=info \
    --log-file=/src/logs/gunicorn.log \
    --access-logfile=/src/logs/access.log \
    project.wsgi:application
