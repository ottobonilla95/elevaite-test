FROM node:20-alpine AS base
 
FROM base AS builder
RUN apk add --no-cache libc6-compat
RUN apk update
# Set working directory
WORKDIR /app
RUN npm install -g turbo
COPY . .
RUN turbo prune elevaite --docker
 
# Add lockfile and package.json's of isolated subworkspace
FROM base AS installer
RUN apk add --no-cache libc6-compat
RUN apk update
WORKDIR /app
 
# First install the dependencies (as they change less often)
COPY .gitignore .gitignore
COPY --from=builder /app/out/json/ .
COPY package.json yarn.lock* package-lock.json* pnpm-lock.yaml* ./
RUN npm ci
 
# Build the project
COPY --from=builder /app/out/full/ .
COPY turbo.json turbo.json
RUN npx --yes turbo run build --filter=elevaite...
 
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1
 
# Don't run production as root
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
USER nextjs
 
COPY --from=installer /app/apps/elevaite/next.config.js .
COPY --from=installer /app/apps/elevaite/package.json .
 
# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=installer --chown=nextjs:nodejs /app/apps/elevaite/.next/standalone ./
COPY --from=installer --chown=nextjs:nodejs /app/apps/elevaite/.next/static ./apps/elevaite/.next/static
COPY --from=installer --chown=nextjs:nodejs /app/apps/elevaite/public ./apps/elevaite/public

USER nextjs

EXPOSE 3101

ENV PORT 3101
 
CMD node apps/elevaite/server.js