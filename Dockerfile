FROM python:3.12-slim

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY app/ app/
COPY tests/ tests/

# Install dependencies
RUN pip install --no-cache-dir .

# Create data directory for SQLite
RUN mkdir -p data

EXPOSE 8000

# Use PORT env var (cloud platforms inject it), default to 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
