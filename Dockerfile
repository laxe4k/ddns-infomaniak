FROM python:3.12-slim

WORKDIR /app

COPY ddns.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "ddns.py"]
