# AI Personal Learning OS

AI Personal Learning OS is the infrastructure foundation for an adaptive learning platform that will eventually build personalized curricula and adjust them as learners progress. This repository currently provides a working web application, API, database, and cache development stack; it intentionally contains no authentication, learning models, or AI features yet.

## Tech stack

- Next.js 14, React, TypeScript, and Tailwind CSS
- FastAPI, SQLAlchemy asyncio, and Alembic
- PostgreSQL 16 and Redis 7
- Docker Compose

## Setup

1. Clone the repository and enter its directory.
2. Copy the backend environment template:

   ```bash
   cp backend/.env.example backend/.env
   ```

3. Build and start the stack:

   ```bash
   docker compose up --build
   ```

4. Visit [http://localhost:3000](http://localhost:3000). The API is available at [http://localhost:8000](http://localhost:8000), with interactive documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

## Project structure

```text
.
|-- frontend/          Next.js App Router frontend
|   |-- app/           Pages, route groups, and global styles
|   |-- components/    Shared UI components
|   `-- lib/           Frontend utilities and API client
|-- backend/           FastAPI backend
|   |-- app/api/       Versioned API routes
|   |-- app/core/      Settings and database infrastructure
|   |-- app/models/    Future database models
|   `-- alembic/       Database migration environment
`-- docker-compose.yml Local development services
```

## Authentication security note

The MVP stores the short-lived access token in browser `localStorage` so the frontend can attach it to API requests. Refresh tokens are never written to JavaScript-accessible storage; the backend also issues them as HTTP-only, same-site cookies. A production hardening pass should move the access token to an in-memory or fully cookie-based session strategy and enable secure cookies over HTTPS.
