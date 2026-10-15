FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Ensure upload directory exists
RUN mkdir -p /app/uploads

# Expose default port
EXPOSE 8000

# Apply migrations before starting the API. The migration entry point can adopt
# the known existing 001-006 schema in production when Alembic has no version row.
CMD ["sh", "-c", "python -m app.core.migrate && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
