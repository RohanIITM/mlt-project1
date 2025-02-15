FROM python:3.12-slim-bookworm

# Install Node.js and npm (which includes npx)
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the necessary files from the UV image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory
WORKDIR /app
COPY . /app

# Set the PATH for the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Install Python dependencies
RUN uv sync --frozen

# Expose the port that FastAPI runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
