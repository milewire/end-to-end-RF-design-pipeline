FROM python:3.12-slim

# Upgrade system packages and OpenSSL to fix vulnerabilities
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get dist-upgrade -y && \
    apt-get install -y --only-upgrade openssl build-essential libffi-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r requirements.txt

COPY outputs/rf_model.pkl ./outputs/rf_model.pkl
COPY serve.py .

EXPOSE 8080
CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8080"]


