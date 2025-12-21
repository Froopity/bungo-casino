#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
uv run yoyo apply --database "sqlite:///${DATABASE_PATH}" --batch

# Start the bot
echo "Starting casino bot..."
exec uv run python -m casino.bot
