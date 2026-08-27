# Architecture — URL Shortener Service

## 1. High-level approach

This is a small, single-domain service (one core entity: `URL`, one secondary entity: `Visit`), read-heavy on the hot path (`GET /{short_code}`), and explicitly graded on scalability thinking, not feature breadth. That shapes every decision below.

**Chosen style: Layered architecture with a repository layer, fully async.**

## 2. Project structure

```
url-shortener/
├── app/
│   ├── main.py                 # FastAPI app factory, router registration, middleware, health check
│   ├── api/
│   │   ├── urls.py              # /shorten, /{short_code}, /stats/{short_code}
│   │   └── health.py            # /health — DB connectivity check
│   ├── core/
│   │   ├── config.py            # pydantic-settings, reads from env / .env
│   │   ├── database.py          # async engine, session factory, pooling config
│   │   ├── logging.py           # structured logging setup + request-id middleware
│   │   └── exceptions.py        # domain exceptions + FastAPI exception handlers
│   ├── models/
│   │   └── url.py               # SQLAlchemy ORM: URL, Visit
│   ├── schemas/
│   │   └── url.py               # Pydantic request/response models
│   ├── services/
│   │   └── shortener.py         # business logic: code generation, orchestration
│   └── repositories/
│       └── url_repository.py    # all DB queries live here, nowhere else
├── alembic/
│   ├── env.py                   # configured for async engine + Base.metadata
│   └── versions/
│       └── 0001_create_urls_and_visits.py
├── alembic.ini
├── tests/
│   ├── conftest.py               # async test client + test DB fixture
│   ├── test_shorten.py
│   ├── test_redirect.py
│   └── test_stats.py
├── docker-compose.yml           # api + postgres (+ redis, if caching added)
├── Dockerfile
├── requirements.txt
├── .env.example
├── SCALABILITY.md
└── README.md
```

**Why each piece is separated this way:**

- **`api/` never talks to the DB directly.** Routers only: parse request → call service → shape response → raise HTTP errors via registered exception handlers. This keeps HTTP concerns (status codes, request parsing) out of business logic, so `services/` stays testable without spinning up FastAPI at all.
- **`services/` holds the one piece of actual logic**: how a short code gets generated and assigned. It depends on `repositories/`, never on `models/` SQLAlchemy internals directly, and never on FastAPI.
- **`repositories/` is the single place that writes SQL/ORM queries.** If we ever swap Postgres for something else, or add caching in front of reads, this is the only layer that changes.
- **`core/database.py`** owns the async engine and connection pool, created once at import time — not per-request — satisfying the "no new DB connection per request" requirement directly.
- **`core/exceptions.py`** — domain-level exceptions (`ShortCodeNotFoundError`) raised in `services/`, translated to HTTP responses by a registered FastAPI exception handler. Services stay decoupled from HTTP status codes entirely.
- **`core/logging.py`** — a middleware assigns a `request_id` (uuid4) to every request and binds it into structured log context, so concurrent async requests produce traceable, non-interleaved logs. Visit logging itself happens via `BackgroundTasks` with its own DB session (not the request's session — see SCALABILITY.md for why), so the redirect response is never delayed by the log write.
