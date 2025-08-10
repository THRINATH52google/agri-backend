FROM python:3.11-slim

# Install system dependencies including FFmpeg and Git
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Upgrade pip & set retry settings
RUN pip install --upgrade pip setuptools wheel \
    && pip config set global.timeout 100 \
    && pip config set global.retries 10

# Install Python dependencies with retries & no cache
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.org/simple

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

