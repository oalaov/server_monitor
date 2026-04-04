FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alerts.py .

RUN mkdir -p /app/data

# Запускаем бота (вызываем функцию run из alerts.py)
CMD ["python", "-c", "from alerts import run; run()"]