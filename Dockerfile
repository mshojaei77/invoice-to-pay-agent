# =============================================================================
# Stage 0: base — install system deps + Python dependencies via uv
# =============================================================================
FROM python:3.11-slim AS base

# Install system libraries required by docling (OpenCV, GL, etc.)
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# First copy only dependency metadata for Docker layer caching
COPY pyproject.toml uv.lock ./

# Install project dependencies from lock file (no dev extras)
# Project itself is NOT installed yet — only third-party deps for layer caching
RUN uv sync --frozen --no-dev --no-install-project

# Now copy the rest of the application source
COPY app/ app/
COPY scripts/ scripts/

# Copy sample documents and ensure the data directory exists
COPY samples/ samples/
RUN mkdir -p data/processed data/raw

# Install the project itself (source already in place)
RUN uv sync --frozen --no-dev

# =============================================================================
# Stage 1: api — FastAPI / Uvicorn server
# =============================================================================
FROM base AS api

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# =============================================================================
# Stage 2: ui — Streamlit review UI
# =============================================================================
FROM base AS ui

EXPOSE 8501
CMD ["uv", "run", "streamlit", "run", "app/ui/streamlit_app.py", \
     "--server.port=8501", \
     "--server.headless=true", \
     "--server.address=0.0.0.0"]
