#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade "pip==23.3.2"
pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate