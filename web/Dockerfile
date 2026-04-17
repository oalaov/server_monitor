FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY webmonFlask.py .
COPY templates ./templates

RUN mkdir -p /app/data

EXPOSE 5000

CMD ["python", "-c", "from webmonFlask import app, init_db; init_db(); app.run(host='0.0.0.0', port=5000)"]