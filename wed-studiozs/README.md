# WED STUDIOZS

A photography website and studio workspace, served by one FastAPI application.
Jinja templates, local CSS, and plain JavaScript keep the frontend in the same
deployable artifact. There is no Node build, separate frontend service, or
Bootstrap CDN dependency.

## What the application does

| Visitor | Studio administrator |
|---|---|
| Browse the photography journal and published collections | Publish and maintain portfolios |
| Open photographs in a keyboard-accessible lightbox | Manage gallery image URLs |
| Search and filter by occasion | Review enquiries and update their status |
| Enquire about an event | Manage consultation requests |
| Request a consultation | Read and manage contact messages |
| Contact the studio | Sign in and sign out of the protected workspace |

Customer forms work without JavaScript. Invalid submissions retain the entered
values and show field-specific errors. Successful submissions redirect to a
short-lived private receipt, so refreshing the confirmation page does not
submit the form again. A consultation request is not an automatically confirmed
appointment. Messages are saved to the database; this application does not send
email or Instagram DMs.

## Photography and content

The user supplied [@wed_studiozs](https://www.instagram.com/wed_studiozs/) as the
portfolio source. Five publicly visible photo posts are stored locally under
`app/static/img`, preserving the original artwork and attribution.

- `app/web/journal.py` contains the curated stories and original post links.
- `app/static/img/sources.json` records provenance.
- This is a **curated snapshot**, not an automatically refreshed Instagram feed.
- These preview photographs are approximately 512 x 640 pixels. Replace them
  with the studio's high-resolution originals for larger displays.
- The journal is application content; database-backed **Studio collections** are
  managed separately through the admin workspace.
- There are no invented statistics, testimonials, delivery guarantees, or prices.
- Demo database content is opt-in and is not created during startup.

Use permanent HTTPS image URLs or bundled `/static/` image paths when publishing
collections. Upload storage is not implemented. Expiring Instagram CDN URLs are
not suitable for published collections.

## Run locally

Run these commands from `wed-studiozs`, in an activated Python 3.12+ virtual
environment. Use a development database, not a production database.

1. Install application and development dependencies:

   ```text
   python -m pip install -r requirements-dev.txt
   ```

   The production dependency list is `requirements.txt`. The virtual environment
   and dependency installation do not need to be included in the source tree.

2. Set configuration using environment variables or a local `.env` based on
   `.env.example`. Supply a database URL and a random `SECRET_KEY` of at least
   32 characters. The signing key must be identical for every application replica.
   Do not commit it.

3. Apply the schema explicitly:

   ```text
   alembic upgrade head
   ```

4. Create your administrator explicitly:

   ```text
   python -m app.cli create-admin --email you@example.com
   ```

   Supply the password through the hidden prompt, never as a command-line
   argument. There is no built-in administrator or default login password.

5. Start the application:

   ```text
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-graceful-shutdown 40
   ```

   Open `http://localhost:8000` for the website and
   `http://localhost:8000/admin` for the studio workspace.

## Developer-to-DevOps handoff

The infrastructure remains the DevOps engineer's responsibility. No Dockerfile,
Compose, Kubernetes, CI/CD, or cloud configuration is maintained by this change.

| Application contract | What the platform must provide |
|---|---|
| A single HTTP process on port 8000 | Build and deploy the application image |
| Required shared signing key | Inject `SECRET_KEY`, including into the migration Job while settings are shared |
| Explicit schema management | Run Alembic once per release, wait for success, then roll out application pods |
| Explicit administrator creation | Run the bootstrap CLI once per environment with protected input |
| `/healthz`: process liveness, no database I/O | Use for startup/liveness, not a database check |
| `/readyz`: database and required schema are usable | Use for readiness with a timeout longer than the application's internal deadline |
| `/metrics`: Prometheus exposition | Configure scraping and restrict access appropriately |
| JSON logs with request IDs | Collect stdout/stderr; retain the request ID for investigation |
| Non-root, read-only-root compatible application | Supply a writable temporary directory and suitable pod security settings |
| Uvicorn graceful shutdown and database cleanup | Allow enough grace time for preStop, request drain, and cleanup |
| Browser admin session cookies are Secure in production | Terminate HTTPS correctly and set production configuration |

Startup does not create tables or seed users. A reachable database without a
compatible schema is not a ready application. Additional database tables and
columns are allowed so compatible expand/contract releases can coexist.

The default application pool allows 5 persistent connections plus 10 overflow
connections **per worker process**. Budget for workers, replicas, surge pods,
terminating pods, migrations, and operator connections. Set pool values through
configuration; adding workers also multiplies the pool budget.

Runtime dependencies changed. The current offline Docker build requires a
wheelhouse supplied by the platform owner: refresh that artifact for the new
`requirements.txt`, including transitive dependencies. Rebuilding source alone
does not supply missing offline wheels.

## Authentication

The browser workspace uses an HttpOnly session cookie, with CSRF protection on
cookie-authenticated changes. JavaScript does not store the administrator JWT
in localStorage. The existing bearer-token API remains available for API clients.
An expired or invalid browser session requires signing in again.

Public confirmation receipts are short-lived signed cookies, not authentication
tokens. An enquiry ID alone does not reveal another customer's details.

## Existing REST API

Interactive API documentation remains at `/docs`. Main routes:

| Prefix | Purpose |
|---|---|
| `/api/v1/auth` | Login, current administrator, administrator creation |
| `/api/v1/portfolios` | Portfolios, featured collections, nested gallery operations |
| `/api/v1/images` | Individual gallery image updates/deletion |
| `/api/v1/inquiries` | Public submission and protected enquiry management |
| `/api/v1/bookings` | Public consultation requests and protected management |
| `/api/v1/contact` | Business details, public messages, protected message management |

Protected API requests accept `Authorization: Bearer <token>`. Domain errors keep
the existing `{"error": {"code": "...", "message": "...", "details": {}}}` envelope.
List responses contain `items`, `total`, `page`, `size`, and `pages`.

## Development checks

```text
python -m pytest -q
```

The suite covers API behavior, customer forms, publishing validation, session
protection, administrative workflows, lifecycle/readiness, logs, metrics, and
bootstrap commands. Its default database fixtures use SQLite; that is not a
substitute for running integration checks against PostgreSQL in your pipeline.
Run migrations against a fresh PostgreSQL database in CI as well.

## Application layout

```text
app/
  api/          Existing REST endpoints and authentication dependencies
  core/         Runtime configuration, errors, authentication and logging helpers
  db/           Sessions, readiness/schema checks and explicit seed utilities
  models/       Database models
  repositories/ Database access
  schemas/      Input and response contracts
  services/     Business rules
  web/          Public pages, private receipts, curated journal and admin routes
  templates/    Server-rendered public and admin pages
  static/       Locally served styles, scripts and studio photographs
alembic/        Explicit schema migrations
tests/          Regression coverage
```
