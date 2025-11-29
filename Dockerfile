# Use an official lightweight Python image
# Use a specific tag to avoid surprises (slim-bullseye is stable)
FROM python:3.11-slim-bullseye

# Set working directory
WORKDIR /app

# Avoid Python buffering so logs appear immediately
ENV PYTHONUNBUFFERED=1

# Install system deps required for some Python packages (if any)
# Keep it minimal; add more if some dependency needs build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app code
COPY . .

# Expose the port the Flask app listens on (your app uses 8080)
EXPOSE 8080

# Ensure the container starts the app using environment variables for DB URI
# Do NOT bake secrets into the image; pass them via env or k8s ConfigMap/Secret
CMD ["python3", "app.py"]