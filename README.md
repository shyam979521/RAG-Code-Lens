# RAG CodeLens

RAG CodeLens is a Flask application for uploading source-code archives, browsing
their contents, generating code explanations and README drafts, and viewing
dependency relationships.

## Architecture

The active application entry point is `app.py`. It owns Flask startup and route
registration while delegating reusable filesystem and project-discovery logic to
the application package.

```
app/
  config/       Central configuration
  models/       SQLAlchemy models
  routes/       Route module scaffold for the next refactor checkpoint
  services/     RAG, LLM, vector, dependency, and project services
  utils/        Shared filesystem utilities
templates/      Existing server-rendered templates
app.py          Flask entry point and current route definitions
config.py       Backward-compatible Config import
```

## Installation

Create and activate a virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

Set `GROQ_API_KEY` before using AI features. The application also accepts these
configuration overrides: `SECRET_KEY`, `DATABASE_URL`, `UPLOAD_FOLDER`,
`VECTOR_INDEX_PATH`, and `LLM_MODEL`.

## Run

```bash
python app.py
```

The application runs on `http://127.0.0.1:5000` by default. Uploaded archives
are extracted into the configured upload folder and metadata is stored in the
configured SQLite database by default.

## Development notes

- Keep user-facing routes and template URLs stable.
- Put reusable filesystem behavior in `app/utils`.
- Put reusable application behavior in `app/services`.
- The next refactor checkpoint will move the active route handlers into the
  existing route package without changing their URLs or responses.

## Authentication

Authentication uses the existing server-side Flask session and Werkzeug password
hashing. Login and registration remain available at `/login` and `/register`;
protected pages redirect unauthenticated visitors to sign in. Selecting
“Remember me” creates a seven-day permanent session; other sessions end with the
browser session. Session cookies are HTTP-only and use a `Lax` same-site policy.

Password recovery and reset pages are UI placeholders only. Configure a mail
provider, signed reset tokens, expiry, and rate limiting before enabling actual
password-reset delivery in production.

## Dashboard foundation

The authenticated dashboard uses a reusable application shell with a responsive
sidebar, top bar, breadcrumb, dashboard content area, and future-module
placeholders. Existing project operations remain server-rendered and retain
their URLs. Future workspace modules currently use lightweight client-side
placeholders so no new backend routes or API contracts are introduced.

## Project workspace

Upload continues to use the existing `/api/upload` ZIP pipeline. Once extracted,
projects can be opened at `/workspace/<project-name>` for read-only browsing.
The workspace builds a lightweight folder tree, shows file metadata and detected
extensions, and reads a selected source file only when requested. ZIP archives
remain the only accepted upload format; folder upload and browser-side archive
creation are intentionally not implemented.

Ignored directories follow the configured project filters, including `.git`,
`node_modules`, virtual environments, and Python cache directories. The current
indexing pipeline stores Python, JavaScript, HTML, CSS, text, Markdown, and JSON
files; the explorer can display other non-ignored extracted files when present.
