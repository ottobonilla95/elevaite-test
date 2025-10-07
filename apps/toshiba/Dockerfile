FROM node:20-alpine AS base

FROM base AS builder
RUN apk add --no-cache libc6-compat
RUN apk update

# Set working directory
WORKDIR /app
RUN npm install -g turbo
COPY . .
RUN turbo prune toshiba --docker

# Add lockfile and package.json's of isolated subworkspace
FROM base AS installer
RUN apk add --no-cache libc6-compat
RUN apk update
WORKDIR /app

# Accept build-time env vars - FIXED FORMAT
ARG NEXT_PUBLIC_BACKEND_URL
ENV NEXT_PUBLIC_BACKEND_URL=${NEXT_PUBLIC_BACKEND_URL}
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ARG NEXT_PUBLIC_AUTH_API_URL
ENV NEXT_PUBLIC_AUTH_API_URL=${NEXT_PUBLIC_AUTH_API_URL}
ARG NEXT_PUBLIC_AUTH_TENANT_ID
ENV NEXT_PUBLIC_AUTH_TENANT_ID=${NEXT_PUBLIC_AUTH_TENANT_ID}
ARG NEXT_PUBLIC_MFA_METHODS_ENABLED
ENV NEXT_PUBLIC_MFA_METHODS_ENABLED=${NEXT_PUBLIC_MFA_METHODS_ENABLED}
ARG NEXT_PUBLIC_MFA_ALLOW_DISABLE_ALL
ENV NEXT_PUBLIC_MFA_ALLOW_DISABLE_ALL=${NEXT_PUBLIC_MFA_ALLOW_DISABLE_ALL}

# First install the dependencies (as they change less often)
COPY .gitignore .gitignore
COPY --from=builder /app/out/json/ .
COPY package.json yarn.lock* package-lock.json* pnpm-lock.yaml* ./

# Clear cache and install dependencies
RUN npm cache clear --force
RUN npm ci

# Build the project with the env injected
COPY --from=builder /app/out/full/ .
COPY turbo.json turbo.json

# Build with proper environment variables
RUN npx --yes turbo run build --filter=toshiba...

FROM base AS runner
WORKDIR /app

# FIXED: Use proper ENV format
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Don't run production as root
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=installer /app/apps/toshiba/next.config.mjs .
COPY --from=installer /app/apps/toshiba/package.json .

# Automatically leverage output traces to reduce image size
COPY --from=installer --chown=nextjs:nodejs /app/apps/toshiba/.next/standalone ./
COPY --from=installer --chown=nextjs:nodejs /app/apps/toshiba/.next/static ./apps/toshiba/.next/static
COPY --from=installer --chown=nextjs:nodejs /app/apps/toshiba/public ./apps/toshiba/public

USER nextjs

EXPOSE 3101
ENV PORT=3101

# FIXED: Use JSON format for CMD
CMD ["node", "apps/toshiba/server.js"]