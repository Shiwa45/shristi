#!/bin/bash
cd /var/task
python manage.py migrate --noinput
python manage.py collectstatic --noinput
