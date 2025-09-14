# Orchestrator Platform - Docker Image
# Multi-stage build for development and production deployment

# Base stage with common dependencies
FROM python:3.9-slim-bullseye as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 18.x
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Create orchestrator user
RUN useradd -r -m -d /opt/orchestrator -s /bin/bash orchestrator

# Set working directory
WORKDIR /opt/orchestrator

# Development stage
FROM base as development

# Install development tools
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    tree \
    mosquitto \
    mosquitto-clients \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt hal_service/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Node-RED and dashboard
RUN npm install -g --unsafe-perm node-red@3.1.0 node-red-dashboard

# Copy project files
COPY . .

# Set ownership
RUN chown -R orchestrator:orchestrator /opt/orchestrator

# Switch to orchestrator user
USER orchestrator

# Create Node-RED directory
RUN mkdir -p /opt/orchestrator/.node-red

# Expose ports
EXPOSE 1880 1883

# Development command
CMD ["bash", "-c", "mosquitto -d && node-red --settings /opt/orchestrator/configs/node_red_config/settings.js"]

# Production stage
FROM base as production

# Install only production dependencies
RUN apt-get update && apt-get install -y \
    mosquitto \
    mosquitto-clients \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Node-RED
RUN npm install -g --unsafe-perm node-red@3.1.0 node-red-dashboard

# Copy only necessary files
COPY hal_service/ ./hal_service/
COPY configs/ ./configs/
COPY *.py ./
COPY config.yaml ./

# Set ownership
RUN chown -R orchestrator:orchestrator /opt/orchestrator

# Switch to orchestrator user
USER orchestrator

# Create directories
RUN mkdir -p /opt/orchestrator/{logs,.node-red}

# Copy Node-RED configuration
RUN cp -r /opt/orchestrator/configs/node_red_config/* /opt/orchestrator/.node-red/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:1880 || exit 1

# Expose ports
EXPOSE 1880 1883

# Production command
CMD ["bash", "-c", "mosquitto -d && node-red --settings /opt/orchestrator/.node-red/settings.js"]