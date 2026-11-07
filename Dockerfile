FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOST=0.0.0.0 PORT=5000
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
COPY requirements-prod.txt ./requirements-prod.txt
RUN python -m pip install --no-cache-dir --upgrade pip && python -m pip install --no-cache-dir -r requirements-prod.txt
COPY . .
RUN useradd --create-home --uid 10001 travesia && mkdir -p /app/instance && chown -R travesia:travesia /app
USER travesia
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/api/health' % os.environ.get('PORT', '5000'), timeout=4)" || exit 1
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --threads 8 --timeout 120 app:application"]
