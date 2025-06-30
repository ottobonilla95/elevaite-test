FROM node:20-slim

# Set working directory
WORKDIR /app

# Copy the entire monorepo
COPY . .

# Install dependencies
WORKDIR /app
RUN npm install -g turbo
RUN turbo prune --scope=MediaIngest --docker

# Install dependencies for the MediaIngest app
WORKDIR /app/out/full
RUN npm install

# Build the app
RUN npm run build --filter=MediaIngest

# Expose the port
EXPOSE 3011
ENV PORT=3011

# Start the application
WORKDIR /app/out/full/apps/MediaIngest
CMD ["npm", "run", "start"]
