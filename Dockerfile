# Multi-stage build for Academic Paper Assistant

# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production

COPY frontend/ .
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libreoffice-writer \
    fonts-dejavu \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY agents/ ./agents/
COPY skills/ ./skills/
COPY knowledge/ ./knowledge/
COPY config.py .

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create output directory
RUN mkdir -p output

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/status || exit 1

# Run the application
CMD ["python", "backend/api.py"]
