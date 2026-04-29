# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/client
COPY client/package*.json ./
RUN npm install
COPY client/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim AS backend
WORKDIR /app/server

# Install Python dependencies
COPY server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY server/ ./

# Copy built frontend into expected location
COPY --from=frontend-builder /app/client/dist ../client/dist

# Expose port
EXPOSE 8080

# Environment
ENV PORT=8080
ENV NODE_ENV=production
ENV PYTHONUNBUFFERED=1

# Start FastAPI with uvicorn
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
