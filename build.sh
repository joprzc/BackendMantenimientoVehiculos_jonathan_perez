#!/usr/bin/env bash
set -o errexit

pip install -r app1/requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --noinput
