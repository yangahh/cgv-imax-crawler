FROM python:3.9
RUN apt-get update && apt-get -y install cron vim wget unzip curl jq systemd

# Install latest Chrome
RUN CHROME_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq -r '.channels.Stable.downloads.chrome[] | select(.platform == "linux64") | .url') \
    && curl -sSLf --retry 3 --output /tmp/chrome-linux64.zip "$CHROME_URL" \
    && unzip /tmp/chrome-linux64.zip -d /opt \
    && ln -s /opt/chrome-linux64/chrome /usr/local/bin/chrome \
    && rm /tmp/chrome-linux64.zip

RUN CHROMEDRIVER_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform == "linux64") | .url') \
    && curl -sSLf --retry 3 --output /tmp/chromedriver-linux64.zip "$CHROMEDRIVER_URL" \
    && unzip -o /tmp/chromedriver-linux64.zip -d /tmp \
    && rm -rf /tmp/chromedriver-linux64.zip \
    && mv -f /tmp/chromedriver-linux64/chromedriver "/usr/local/bin/chromedriver" \
    && chmod +x "/usr/local/bin/chromedriver"

RUN apt-get install -y chromium chromium-driver

WORKDIR /app/src

COPY ["requirements.txt", "main.py", ".env", "./"]
COPY ["entrypoint.sh", "/usr/sbin/"]

RUN chmod +x /app/src/main.py
RUN chmod 777 /usr/sbin/entrypoint.sh

RUN pip install --upgrade pip
RUN pip install -r ./requirements.txt

ENTRYPOINT ["/usr/sbin/entrypoint.sh"]