# Use official Python 3.10 image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (OpenCV, InsightFace, Node.js, curl)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20 LTS (required for Hardhat local blockchain)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy and install Node.js dependencies (Hardhat)
COPY package.json hardhat.config.js ./
RUN npm install --production

# Create cache directory for InsightFace models
RUN mkdir -p /.insightface && chmod 777 /.insightface
ENV INSIGHTFACE_HOME=/.insightface

# Copy all code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose ports (7860 = API, 8545 = Hardhat RPC)
EXPOSE 7860 8545

# Entrypoint: start Hardhat → deploy contract → start API
CMD ["./entrypoint.sh"]
