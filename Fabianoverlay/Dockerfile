# Use an official lightweight Python image
FROM python:3.11-slim

# Minimal, portable Dockerfile — avoid apt installs so it's more likely to build on PaaS
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=app.py

WORKDIR /app

# Copy requirements and install. Keep layers small and use --no-cache-dir
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# Copy application
COPY . /app

# Expose port used by the app
EXPOSE 5000

# Entrypoint: run gunicorn as the WSGI server. Back4app expects a CMD or process to start.
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app", "--workers", "2", "--threads", "2"]
