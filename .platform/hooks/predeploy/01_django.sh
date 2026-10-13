#!/bin/bash
set -euo pipefail

# EB runs predeploy as root from /var/app/staging after installing dependencies.
source /var/app/venv/*/bin/activate
install -d -m 0750 -o webapp -g webapp /var/app/data
python manage.py migrate --noinput
python manage.py seed_polls
python manage.py collectstatic --noinput
chown webapp:webapp /var/app/data/db.sqlite3
chmod 0600 /var/app/data/db.sqlite3
