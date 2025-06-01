FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir feedparser requests

COPY app /app/

CMD ["python", "-u", "notify.py"]
