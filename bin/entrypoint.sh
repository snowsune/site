#!/bin/sh

./manage.py makemigrations
./manage.py migrate

# Generate initial sitemap
./manage.py ensure_sitemap

# Add cron job to regenerate sitemap every hour
echo "0 */6 * * * /app/manage.py ensure_sitemap >> /var/log/cron.log 2>&1" | crontab -

# Start cron daemon
service cron start

# Start the application
gunicorn snowsune.wsgi:application --bind 0.0.0.0:80 --workers 4