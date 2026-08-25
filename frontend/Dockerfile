# Development image for the Next.js frontend.
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --no-audit --no-fund --fetch-retries=5 --fetch-retry-mintimeout=20000 --fetch-retry-maxtimeout=120000

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
