FROM node:20-slim

# Set working directory
WORKDIR /app

# Copy the entire monorepo
COPY . .

# Install dependencies
WORKDIR /app
RUN npm install -g turbo
RUN turbo prune --scope=pipelines --docker

# Install dependencies for the pipelines app
WORKDIR /app/out/full
RUN npm install

# Build the app
RUN npm run build --filter=pipelines

# Expose the port
EXPOSE 3010
ENV PORT=3010

# Start the application
WORKDIR /app/out/full/apps/pipelines
CMD ["npm", "run", "start"]
