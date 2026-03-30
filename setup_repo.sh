#!/usr/bin/env bash

set -e

PROJECT_NAME="gradebook"

echo "Creating project structure..."

mkdir -p backend/app
mkdir -p backend/app/models
mkdir -p backend/app/schemas
mkdir -p backend/app/routers
mkdir -p backend/app/services

mkdir -p frontend
mkdir -p database
mkdir -p scripts

touch README.md
touch docker-compose.yml

echo "Initializing Python backend..."

cd backend

#!/usr/bin/env bash
# Create and set up a new conda environment for the project

ENV_NAME=$PROJECT_NAME
PYTHON_VERSION="3.11"

echo "Creating conda environment '${ENV_NAME}' with Python ${PYTHON_VERSION}..."

# Create the environment (using mamba if available, otherwise conda)
if command -v mamba >/dev/null 2>&1; then
  echo "Using mamba to create environment..."
  mamba create -y -n "${ENV_NAME}" python=${PYTHON_VERSION}
elif command -v conda >/dev/null 2>&1; then
  echo "Using conda to create environment..."
  conda create -y -n "${ENV_NAME}" python=${PYTHON_VERSION}
else
  echo "Error: Neither mamba nor conda found. Please install conda or mamba first."
  exit 1
fi

# Activate the environment
echo "Activating environment '${ENV_NAME}'..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "${ENV_NAME}"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing project dependencies..."
if command -v mamba >/dev/null 2>&1; then
  echo "Using mamba for package installation..."
  mamba install -y \
    fastapi \
    uvicorn \
    sqlalchemy \
    psycopg2-binary \
    alembic \
    pydantic \
    python-dotenv \
    pytest \
    httpx
elif command -v conda >/dev/null 2>&1; then
  echo "Using conda for package installation..."
  conda install -y \
    fastapi \
    uvicorn \
    sqlalchemy \
    psycopg2-binary \
    alembic \
    pydantic \
    python-dotenv \
    pytest \
    httpx
else
  echo "Using pip for package installation..."
  pip install \
    fastapi \
    uvicorn \
    sqlalchemy \
    psycopg2-binary \
    alembic \
    pydantic \
    python-dotenv \
    pytest \
    httpx
fi

# Generate requirements.txt
echo "Generating requirements.txt..."
pip freeze >requirements.txt

echo "Setup completed successfully."
echo "Environment '${ENV_NAME}' is now active."
echo "To reactivate later, run: conda activate ${ENV_NAME}"

echo "Creating backend skeleton..."

touch app/main.py
touch app/database.py
touch app/config.py

touch app/models/__init__.py
touch app/schemas/__init__.py
touch app/routers/__init__.py
touch app/services/__init__.py

touch app/routers/teachers.py
touch app/routers/students.py
touch app/routers/classes.py
touch app/routers/enrollments.py
touch app/routers/exams.py
touch app/routers/results.py

cd ..

echo "Initializing Alembic..."

cd backend
alembic init migrations
cd ..

echo "Creating frontend structure..."

cd frontend

mkdir -p shiny_app
touch shiny_app/app.R

echo "Initializing R environment with renv..."

# Ensure R exists
if ! command -v R >/dev/null 2>&1; then
  echo "Error: R is not installed or not in PATH."
  exit 1
fi

cd shiny_app

# Create renv project
R -q -e "install.packages('renv', repos='https://cloud.r-project.org')"
R -q -e "renv::init(bare = TRUE)"

echo "Installing required R packages..."

R -q -e "install.packages(c(
  'shiny',
  'r6',
  'httr2',
  'tidyverse',
  'jsonlite',
  'glue',
  'DT'
), repos='https://cloud.r-project.org')"

echo "Snapshotting renv environment..."

R -q -e "renv::snapshot()"

cd ..
cd ..

echo "Creating database initialization directory..."

cd database
touch init.sql
cd ..

echo "Creating Dockerfiles..."

cat <<EOF >backend/Dockerfile
FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

cat <<EOF >frontend/Dockerfile
FROM rocker/shiny

WORKDIR /srv/shiny-server

COPY shiny_app/ /srv/shiny-server/

EXPOSE 3838
EOF

echo "Creating docker-compose..."

cat <<EOF >docker-compose.yml
version: "3.9"

services:

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: gradebook
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    depends_on:
      - db
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    depends_on:
      - backend
    ports:
      - "3838:3838"

volumes:
  postgres_data:
EOF

echo "Repository setup complete."

echo "Next steps:"
echo "1. cd $PROJECT_NAME/backend"
echo "2. source venv/bin/activate"
echo "3. Start writing SQLAlchemy models"
echo "4. Run docker compose up"
