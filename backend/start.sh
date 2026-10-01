#!/usr/bin/env bash
set -e

echo "=== [EnglishLearningAgent Production Startup] ==="

# Collect static files for WhiteNoise
echo "--> Collecting static assets..."
python manage.py collectstatic --noinput

# Run database migrations
echo "--> Running database migrations..."
python manage.py migrate --noinput

# Load pre-seeded data fixture (recordings, historical sessions, exercises, users)
if [ -f "initial_data.json" ]; then
    echo "--> Loading initial data fixture..."
    python manage.py loaddata initial_data.json || true
fi

# Seed default practice exercises (A1 to C2)
echo "--> Seeding practice exercises..."
python manage.py seed_exercises

# Start Celery worker in background if not in synchronous eager mode
if [ "$CELERY_TASK_ALWAYS_EAGER" != "True" ] && [ "$CELERY_TASK_ALWAYS_EAGER" != "true" ] && [ -n "$CELERY_BROKER_URL" ]; then
    echo "--> Starting background Celery worker (concurrency=2)..."
    celery -A core worker --loglevel=info --concurrency=2 &
else
    echo "--> Celery worker running in synchronous eager mode (CELERY_TASK_ALWAYS_EAGER=True)."
fi

# Start Gunicorn server
PORT="${PORT:-8000}"
echo "--> Launching Gunicorn WSGI server on port $PORT..."
exec gunicorn core.wsgi:application --bind "0.0.0.0:$PORT" --workers 2 --timeout 120
