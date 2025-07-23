FROM node:20-alpine AS base

FROM base AS builder
RUN apk add --no-cache libc6-compat
RUN apk update
# Set working directory
WORKDIR /app
RUN npm install -g turbo

# Copy only the necessary files for dependency resolution and turbo prune
# This layer will be cached unless package.json files or turbo.json change
COPY package.json yarn.lock* package-lock.json* pnpm-lock.yaml* ./
COPY turbo.json ./

# Copy packages folder and apps folder for turbo prune
# This is more maintainable - automatically includes new packages
COPY packages ./packages
COPY apps ./apps

RUN turbo prune command_agent_version1 --docker

# Add lockfile and package.json's of isolated subworkspace
FROM base AS installer
RUN apk add --no-cache libc6-compat
RUN apk update
WORKDIR /app

# First install the dependencies (as they change less often)
# This layer will be cached unless dependencies change
COPY .gitignore .gitignore
COPY --from=builder /app/out/json/ .
COPY package.json yarn.lock* package-lock.json* pnpm-lock.yaml* ./
RUN npm cache clear --force
RUN npm ci

# Copy source code and build (this layer will be invalidated on source changes)
COPY --from=builder /app/out/full/ .
COPY turbo.json turbo.json
RUN npx --yes turbo run build --filter=command_agent_version1...

FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Don't run production as root
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
USER nextjs

COPY --from=installer /app/apps/command_agent_version1/next.config.mjs .
COPY --from=installer /app/apps/command_agent_version1/package.json .

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=installer --chown=nextjs:nodejs /app/apps/command_agent_version1/.next/standalone ./
COPY --from=installer --chown=nextjs:nodejs /app/apps/command_agent_version1/.next/static ./apps/command_agent_version1/.next/static
#COPY --from=installer --chown=nextjs:nodejs /app/apps/command_agent_version1/public ./apps/command_agent_version1/public

USER nextjs

EXPOSE 3101

ENV PORT=3101

CMD ["node", "apps/command_agent_version1/server.js"]