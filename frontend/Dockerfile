# Frontend Dockerfile for local development only
# Used by docker-compose.local.yml
# Production uses npm build → S3 → CloudFront (see .github/workflows/deploy-*.yml)
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Run Vite in dev mode with host exposed
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
