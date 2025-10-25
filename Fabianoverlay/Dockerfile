# Use an official lightweight Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    FLASK_APP=app.py

# Create app directory
WORKDIR /app

# Install build dependencies and runtime dependencies
COPY requirements.txt /app/requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev libssl-dev build-essential \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && apt-get remove -y gcc build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . /app

# Expose the Flask port
EXPOSE 5000

# Use a non-root user (optional). If you prefer not to, comment these out.
# RUN useradd -m appuser && chown -R appuser /app
# USER appuser

# Default command: run with gunicorn (production-ready)
# Bind to 0.0.0.0:5000 and use 2 workers by default. Adjust as needed.
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app", "--workers", "2", "--threads", "2"]
