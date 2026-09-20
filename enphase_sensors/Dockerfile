FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    config_path=/config

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/*.py ./
COPY scripts/config_example.yaml ./

RUN mkdir /config \
    && useradd --create-home appuser \
    && chown -R appuser:appuser /app /config

USER appuser

CMD ["python", "log_usage.py"]
