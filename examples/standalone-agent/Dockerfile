# Build stage
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy source files
COPY . .

# Production stage
FROM node:22-alpine AS runner

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /app/ ./

EXPOSE 8080
ENV NODE_ENV=production

# Start the server
CMD ["npm", "start"]