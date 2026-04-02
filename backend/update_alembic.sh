#!/usr/bin/env bash
set -e

export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/gradebook

alembic revision --autogenerate -m "${1:-update}"

echo "Migration created successfully."
