FROM python:3.9-slim

# Instalar curl
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements_b.txt .
RUN pip install --no-cache-dir -r requirements_b.txt

COPY app_b.py .

EXPOSE 5001

CMD ["gunicorn", "--bind", "0.0.0.0:5001", "app_b:app"]