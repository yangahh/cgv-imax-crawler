#!/bin/bash

# cron 작업 등록
systemctl enable cron
echo "0 * * * * root python /app/src/main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/crawling-cgv.tmp

# run cron
chmod 644 /etc/cron.d/crawling-cgv.tmp
chown root:root /etc/cron.d/crawling-cgv.tmp

mv /etc/cron.d/crawling-cgv.tmp /etc/cron.d/crawling-cgv

# Load the cron job for root
crontab /etc/cron.d/crawling-cgv

# Start the cron service in the foreground (X)
cron -f
# Start the cron service 
