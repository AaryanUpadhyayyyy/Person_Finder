# Use official Python 3.10 image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (required for OpenCV and InsightFace)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create cache directory for InsightFace models so it has permissions
RUN mkdir -p /.insightface && chmod 777 /.insightface
ENV INSIGHTFACE_HOME=/.insightface

# Copy all code
COPY . .

# Expose port (Hugging Face Spaces uses 7860 by default for Docker)
EXPOSE 7860

# Run the FastAPI app on port 7860
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
