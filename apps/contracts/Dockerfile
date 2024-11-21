FROM node:22-alpine AS base

FROM base AS builder
RUN apk add --no-cache libc6-compat
RUN apk update
# Set working directory
WORKDIR /app
RUN npm install -g turbo
COPY ./apps ./apps
COPY ./packages ./packages
COPY turbo.json package.json package-lock.json ./
RUN turbo prune contracts --docker

# Add lockfile and package.json's of isolated subworkspace
FROM base AS installer
RUN apk add --no-cache libc6-compat
RUN apk update
WORKDIR /app

# First install the dependencies (as they change less often)
COPY .gitignore .gitignore
COPY --from=builder /app/out/json/ .
COPY package.json yarn.lock* package-lock.json* pnpm-lock.yaml* ./
RUN npm cache clear --force 
RUN npm ci

# Build the project
COPY --from=builder /app/out/full/ .
COPY turbo.json turbo.json
RUN npx --yes turbo run build --filter=contracts...

FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Don't run production as root
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
USER nextjs

COPY --from=installer /app/apps/contracts/next.config.js .
COPY --from=installer /app/apps/contracts/package.json .

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=installer --chown=nextjs:nodejs /app/apps/contracts/.next/standalone ./
COPY --from=installer --chown=nextjs:nodejs /app/apps/contracts/.next/static ./apps/contracts/.next/static
COPY --from=installer --chown=nextjs:nodejs /app/apps/contracts/public ./apps/contracts/public

USER nextjs

EXPOSE 3101

ENV PORT=3101

CMD node apps/contracts/server.js