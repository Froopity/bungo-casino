FROM python:3.13-slim

WORKDIR /app

# Install uv for faster dependency management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY yoyo.ini ./
COPY docker-entrypoint.sh ./

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Create directory for database
RUN mkdir -p /data

# Set environment variable for database path
ENV DATABASE_PATH=/data/casino.db

# Run entrypoint script
ENTRYPOINT ["./docker-entrypoint.sh"]
