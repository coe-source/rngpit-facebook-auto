# Use the official Python image as a base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables to avoid python writing .pyc files and to unbuffer stdout
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies required for Playwright and general utilities
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser binaries and their system dependencies
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy the rest of the backend files
COPY . .

# Expose port (Railway provides PORT env variable, but we expose 8000 for local/fallback)
EXPOSE 8000

# Start the FastAPI app using Uvicorn
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
