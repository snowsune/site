#!/bin/sh

./manage.py makemigrations
./manage.py migrate

gunicorn snowsune.wsgi:application --bind 0.0.0.0:80 --workers 4