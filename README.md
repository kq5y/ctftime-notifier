# ctftime-notifier

Retrieve new or one-day-away CTFs from CTFtime.org and announce them in the discord channel.

## Usage

```bash
echo '{}' > app/state.json
```

```bash
```bash
docker build -t ctftime-notifier .
docker run -d \
  --name ctftime-notifier \
  --restart unless-stopped \
  -e DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/XXXXXXXX/XXXXXXXX" \
  -e CTFTIME_RSS_URL="https://ctftime.org/event/list/upcoming/rss/" \
  -e CHECK_INTERVAL="3600" \
  -e TIMEZONE="Asia/Tokyo" \
  -v ./app/state.json:/app/state.json \
  ctftime-notifier
```

## License

[MIT License](LICENSE)
