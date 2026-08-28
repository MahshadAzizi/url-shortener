# URL Shortener Service

A small, production-oriented URL shortener built with **FastAPI**, **SQLAlchemy**, **PostgreSQL**, and **Alembic**.

The service provides short URLs similar to Bitly:

1. A client submits a long URL.
2. The service generates a unique short code.
3. The short code is stored in PostgreSQL.
4. Accessing the short URL redirects to the original URL.
5. Each redirect can be recorded as a visit for statistics.

The implementation focuses on clean architecture, asynchronous I/O, database correctness, performance, and scalability without introducing unnecessary infrastructure.

---

## Features

- Create short URLs
- Redirect short URLs to their original URLs
- Track visit counts
- Record visitor IP addresses
- Request-level structured logging
- Request IDs for tracing
- Async FastAPI endpoints
- Async SQLAlchemy + PostgreSQL
- SQLAlchemy connection pooling
- Unique short-code collision handling
- Alembic database migrations
- Docker and Docker Compose support
- Layered architecture
- Dependency injection through FastAPI
- Stateless API suitable for horizontal scaling

---

# Architecture

The project uses a **layered architecture with a repository layer**.

```text
                         HTTP Request
                              |
                              v
                     +----------------+
                     |   API / Routes |
                     +----------------+
                              |
                              v
                     +----------------+
                     |    Services    |
                     +----------------+
                              |
                              v
                     +----------------+
                     |  Repositories  |
                     +----------------+
                              |
                              v
                     +----------------+
                     |   PostgreSQL   |
                     +----------------+
```

The layers have clear responsibilities:

### API

Responsible for:

- HTTP request/response handling
- Pydantic validation
- HTTP status codes
- Dependency injection
- Calling application services

The API layer does not execute database queries directly.

### Services

Responsible for:

- Business logic
- Short-code generation
- Unique-code collision handling
- Transaction boundaries
- Orchestrating repositories

Services do not depend on FastAPI-specific concepts.

### Repositories

Responsible for:

- Database queries
- Creating and retrieving ORM entities
- Encapsulating SQLAlchemy operations

Repositories do not contain business logic and do not commit transactions.

### Infrastructure

Responsible for:

- Database engine
- Connection pooling
- Async session factory
- Configuration
- External infrastructure concerns

---

# Project Structure

```text
url-shortener/
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── dependencies.py
│   │   ├── middleware.py
│   │   ├── router.py
│   │   │
│   │   └── routes/
│   │       ├── health.py
│   │       └── urls.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   │
│   ├── infrastructure/
│   │   └── database/
│   │       ├── engine.py
│   │       └── session.py
│   │
│   ├── models/
│   │   ├── base.py
│   │   ├── url.py
│   │   └── visit.py
│   │
│   ├── repositories/
│   │   ├── url_repository.py
│   │   └── visit_repository.py
│   │
│   ├── schemas/
│   │   └── url.py
│   │
│   └── services/
│       ├── url_service.py
│       └── visit_service.py
│
├── alembic/
│   ├── env.py
│   └── versions
│
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── SCALABILITY.md
└── README.md
```

---

# API

## Create Short URL

```http
POST /shorten
```

### Request

```json
{
  "original_url": "https://example.com/a/very/long/url"
}
```

### Response

```json
{
  "short_code": "aB91xK2q",
  "short_url": "http://localhost:8000/aB91xK2q",
  "original_url": "https://example.com/a/very/long/url",
  "created_at": "2026-08-28T09:00:00Z"
}
```

Response status:

```text
201 Created
```

---

## Redirect

```http
GET /{short_code}
```

Example:

```http
GET /aB91xK2q
```

The service looks up the short code and redirects to the original URL.

Response:

```text
307 Temporary Redirect
```

The redirect path is intentionally kept lightweight because it is expected to be the highest-volume endpoint.

---

## Statistics

```http
GET /stats/{short_code}
```

Example:

```http
GET /stats/aB91xK2q
```

Response:

```json
{
  "short_code": "aB91xK2q",
  "visits": 42
}
```

---

## Health Check

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

The endpoint is intended for container/orchestrator health checks.

---

# Database Design

The application uses PostgreSQL with two main entities.

## URLs

```text
urls
--------------------------------
id
original_url
short_code
created_at
```

`short_code` has a unique database constraint.

This is important because uniqueness must be guaranteed by the database under concurrent requests.

## Visits

```text
visits
--------------------------------
id
url_id
ip_address
created_at
```

`url_id` references `urls.id`.

The foreign key uses `ON DELETE CASCADE`.

---

# Short Code Generation

Short codes are generated by the application.

The creation algorithm is:

```text
Generate short code
       |
       v
    INSERT
       |
       +------ success ------> return
       |
       +------ collision ----> generate again
```

The service does **not** first query the database to check whether the code exists.

Avoiding this:

```text
SELECT → check → INSERT
```

is important because:

1. It adds an unnecessary database query.
2. It does not prevent race conditions.
3. The database unique constraint already provides the required concurrency guarantee.

Instead, PostgreSQL is the source of truth.

If the unique constraint reports a collision, the service generates another code and retries a bounded number of times.

The retry is limited to the specific `short_code` unique constraint.

---

# Database Access

The application uses SQLAlchemy's async engine and session factory.

The engine and connection pool are created once per application process.

```text
Application process
       |
       v
Async SQLAlchemy Engine
       |
       v
Connection Pool
       |
       v
PostgreSQL
```

A new database connection is **not** created for every HTTP request.

Request-scoped `AsyncSession` instances are created from the shared session factory.

The repository receives an existing session through dependency injection.

Repositories do not create engines or manage global connections.

---

# Dependency Injection

FastAPI dependencies are used as the composition boundary.

For example:

```text
Request
   |
   v
get_db_session()
   |
   v
AsyncSession
   |
   v
URLRepository
   |
   v
URLService
   |
   v
Route
```

This keeps construction concerns outside the service itself.

For visit recording, the service also receives the session factory so that background work can create an independent session.

---

# Transaction Management

Transaction ownership belongs to the service layer.

Repositories perform database operations but do not call:

```python
commit()
```

The service controls the transaction boundary.

For short-code creation, a nested transaction/savepoint is used so a unique-code collision can be rolled back without invalidating the surrounding session.

```text
Service
   |
   +-- begin savepoint
   |
   +-- INSERT
   |
   +-- collision?
   |       |
   |       +--> rollback savepoint
   |       |
   |       +--> generate new code
   |
   +-- commit
```

---

# Logging

The application has two different logging concerns.

## Request Logging

A middleware records information for every HTTP request:

- request ID
- HTTP method
- path
- status code
- client IP
- duration

Example:

```text
2026-08-28 09:20:12 | INFO |
request_id=8c1... |
GET /abc123 |
status=307 |
client=172.27.0.1 |
duration=2.31ms |
request_completed
```

A unique request ID is generated for each request and returned through:

```http
X-Request-ID
```

This allows requests to be correlated across logs.

## Visit Logging

Redirects also generate visit information:

```text
url_id
short_code
ip_address
created_at
```

Visit recording is kept separate from the redirect response path.

The current implementation uses a background task with a **separate database session**.

The request's session must not be reused because its lifecycle is tied to the HTTP request.

At significantly higher traffic, this can be replaced with a durable message queue.

More details are documented in:

```text
SCALABILITY.md
```

---

# Performance Considerations

The redirect endpoint is the hot path.

The lookup is performed using the unique index on `short_code`.

Conceptually:

```sql
SELECT *
FROM urls
WHERE short_code = :short_code
LIMIT 1;
```

The unique index provides efficient lookup at scale.

The service avoids unnecessary database operations such as checking for code existence before insertion.

Visit statistics use an indexed `url_id` column.

---

# Scalability

The application is designed to be stateless.

Multiple API instances can therefore run behind a load balancer:

```text
                 Load Balancer
                /      |      \
               /       |       \
             API      API      API
              |        |        |
              +--------+--------+
                       |
                   PostgreSQL
```

Potential future improvements include:

- Redis for frequently accessed short URLs
- read replicas for PostgreSQL
- a durable queue for visit events
- asynchronous analytics consumers
- pre-aggregated visit counters
- connection pooling with PgBouncer
- horizontal API autoscaling

These are intentionally not part of the initial implementation because they introduce additional operational complexity.

See [`SCALABILITY.md`](SCALABILITY.md) for the reasoning and answers to the scalability scenarios.

---

# Configuration

Configuration is provided through environment variables using `pydantic-settings`.

Example:

```env
APP_NAME=URL Shortener
VERSION=0.1.0
DEBUG=false
ENVIRONMENT=production

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=url_shortener

DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5
DB_POOL_TIMEOUT=30
```

Use:

```text
.env.example
```

as the template for local configuration.

---

# Running Locally

## Prerequisites

- Python 3.12+
- Docker
- Docker Compose

---

## Using Docker Compose

Copy the example environment file:

```bash
cp .env.example .env
```

Start the services:

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/health
```

---

# Database Migrations

Alembic is used for database schema migrations.

Create a migration:

```bash
alembic revision --autogenerate -m "create urls and visits"
```

Apply migrations:

```bash
alembic upgrade head
```

Rollback the latest migration:

```bash
alembic downgrade -1
```

For production deployments, migrations should be executed as an explicit deployment step rather than automatically every time the application starts.

---


# Code Quality Principles

The project follows these principles:

### Single Responsibility

Each layer has one primary responsibility.

```text
API          → HTTP
Service      → business logic
Repository   → persistence
Infrastructure → external resources
```

### Dependency Inversion

Services receive repositories and database dependencies instead of constructing infrastructure internally.

### Don't Repeat Yourself

Common infrastructure such as:

- database sessions
- configuration
- request logging

is centralized.

### Explicit Dependencies

Dependencies are injected rather than hidden in service constructors through global state.

### Async I/O

Database operations use SQLAlchemy's asynchronous API so application workers are not blocked while waiting for PostgreSQL.

### Database Constraints

Correctness that must hold under concurrency is enforced by PostgreSQL rather than application-level checks.

---

# Production Considerations

Before deploying to production, I would additionally consider:

- TLS termination
- secure secret management
- trusted proxy configuration
- rate limiting
- request size limits
- URL validation and SSRF-related considerations
- centralized structured logging
- metrics and tracing
- PostgreSQL backups
- database migration strategy
- container image scanning
- dependency vulnerability scanning
- resource limits for containers
- graceful shutdown
- monitoring and alerting

These concerns are intentionally kept separate from the core URL-shortening implementation.
