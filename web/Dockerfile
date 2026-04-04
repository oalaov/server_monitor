FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости для psutil
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY webmonFlask.py .
COPY templates ./templates

# Создаём папку для базы данных
RUN mkdir -p /app/data

EXPOSE 5000

# Правильный запуск (исправляем проблему с __name__)
CMD ["python", "-c", "from webmonFlask import app, init_db; init_db(); app.run(host='0.0.0.0', port=5000)"]