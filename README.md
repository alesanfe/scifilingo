# SciFiLingo

A Django web application that translates text into 55+ fictional languages (Yoda, Klingon, Sith, Dothraki, Quenya, Elvish, and more) using the [funtranslations.com](https://funtranslations.com) public endpoint. Users can sign up, translate text, browse their history, export it, manage their profile, and switch between English and Spanish.

## Features

### Core
- Translate text into 55+ fictional languages, organized by universe (Tolkien, Star Wars, Star Trek, D&D, etc.)
- User authentication (sign up, login, logout) with real-time form validation
- Per-user translation history with search, filter, pagination, and detail views
- Delete translations with HTMX confirmation modal
- Copy translation to clipboard with visual feedback
- Character counter on the input textarea

### Profile & Settings
- Profile page with statistics (total translations, favorite language, recent activity)
- Change password page (keeps session alive)
- Avatar with user initial, member-since date

### History Export
- Export translation history as **CSV** or **JSON**
- User-scoped (only own translations)

### Internationalization (i18n)
- Full **English** and **Spanish** support
- Language selector (EN/ES) in the navbar
- 100+ translated strings via Django's i18n framework
- Auto-detection via `Accept-Language` header + cookie override

### Security & Performance
- Rate limiting: 10 translations/minute per user (`django-ratelimit`)
- Livewire snapshot caching (5 min per language) to reduce API GET requests
- Secure by default (HSTS, SSL redirect, secure cookies, CSRF protection)
- IDOR protection (users can only access their own translations)

### UI/UX
- Custom sci-fi themed dark UI (Tailwind CSS)
- HTMX for async form submission and modals
- Responsive (mobile + desktop)
- Favicon, SEO meta tags, Open Graph, Twitter Cards
- Custom 403/404/500 error pages

### DevOps
- Deploy-ready for Render (PostgreSQL + WhiteNoise + Gunicorn)
- Multi-stage Dockerfile + `.dockerignore`
- CI/CD with GitHub Actions (linting, tests, deploy checks, auto-deploy)

## Tech Stack

- Python 3.11 / Django 4.2
- django-environ for environment variable management
- django-ratelimit for rate limiting
- SQLite (development) / PostgreSQL (production)
- funtranslations.com Livewire endpoint (bypasses Cloudflare-blocked API)
- Tailwind CSS + HTMX
- WhiteNoise for static files
- Gunicorn as WSGI server
- Ruff for linting and formatting
- pytest + pytest-django for testing (61 tests)

## Setup

```bash
# Clone the repo
git clone https://github.com/alesanfe/scifilingo.git
cd scifilingo

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
.venv\Scripts\activate       # Windows

# Install development dependencies (includes linting + testing tools)
pip install -r requirements-dev.txt

# Set up environment variables
cp .env.example .env         # Linux/macOS
copy .env.example .env       # Windows

# Run migrations
python manage.py migrate

# Compile translations
python manage.py compilemessages

# Create a superuser (optional, for admin access)
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

Visit http://127.0.0.1:8000/translation/ to use the app.

## Environment Variables

Copy `.env.example` to `.env` and adjust as needed:

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | Production | dev key | Django secret key. Auto-generated on Render. |
| `DEBUG` | No | `True` (dev) | Django debug mode. `False` when `RENDER` is set. |
| `ALLOWED_HOSTS` | No | `localhost,...` | Comma-separated list of allowed hosts. |
| `RENDER_EXTERNAL_HOSTNAME` | Auto | empty | Set automatically by Render. |
| `DATABASE_URL` | Production | SQLite | PostgreSQL connection string. Auto-set on Render. |
| `CACHE_BACKEND` | No | `LocMemCache` | Cache backend for ratelimit. Use `RedisCache` in prod. |
| `CACHE_LOCATION` | No | `scifilingo-dev` | Cache location (e.g. `redis://127.0.0.1:6379/1`). |
| `RATELIMIT_ENABLE` | No | `True` | Set to `False` to disable rate limiting. |

## API: funtranslations.com

The app uses the funtranslations.com **Livewire endpoint** (`funtranslations.com/translate/{language}`) instead of the public API (`api.funtranslations.com`), which is blocked by Cloudflare. The API client:

- Simulates a browser session (User-Agent, cookies, CSRF token)
- Fetches the Livewire snapshot from the translation page (cached for 5 min per language)
- POSTs the translation request with the snapshot
- Parses the Livewire JSON response to extract the translated text

Rate limit errors are handled gracefully and shown to the user.

## Development

### Testing

```bash
# Run all tests with pytest
pytest -v

# Run a specific test module
pytest traductor_app/tests/test_views.py -v

# Run with coverage (if pytest-cov installed)
pytest --cov=traductor_app --cov=user_management
```

### Linting and Formatting

```bash
# Check for lint errors
ruff check .

# Auto-fix lint errors
ruff check --fix .

# Format code
ruff format .
```

### Translations

```bash
# Update .po files from templates (requires gettext)
django-admin makemessages -l es

# Compile .po to .mo
django-admin compilemessages
```

### Django Checks

```bash
# System checks
python manage.py check

# Production deployment checks
python manage.py check --deploy
```

## Deployment

### Render (recommended)

1. Fork/push this repo to GitHub.
2. Go to [Render](https://render.com) and create a new Web Service from the repo.
3. The included `render.yaml` defines the service and a PostgreSQL database.
4. For production caching, set `CACHE_BACKEND=django.core.cache.backends.redis.RedisCache` and `CACHE_LOCATION=redis://...`.
5. Render runs `build.sh` (pip install + collectstatic + migrate) and starts Gunicorn automatically.

### Docker

```bash
docker build -t scifilingo .
docker run -p 8000:8000 --env-file .env scifilingo
```

### GitHub Actions

Two workflows are included in `.github/workflows/`:

- **`ci.yml`**: Runs on every push/PR to `main`/`master`.
  - **Lint job**: Ruff check + format check
  - **Test job**: Django system checks, deploy checks, migration consistency, collectstatic, pytest
- **`deploy.yml`**: Triggers on push to `main`. Calls the Render deploy hook URL stored in the `RENDER_DEPLOY_HOOK_URL` repository secret.

## Project Structure

```
scifilingo/
├── manage.py
├── build.sh                      # Build script for Render
├── render.yaml                   # Render service definition
├── Dockerfile                    # Multi-stage Docker build
├── .dockerignore
├── pyproject.toml                # Ruff + pytest config
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Dev dependencies (lint + test)
├── .env.example                  # Example environment variables
├── .github/workflows/
│   ├── ci.yml                    # CI: lint + checks + tests
│   └── deploy.yml                # CD: trigger Render deploy
├── locale/                       # Translations
│   └── es/LC_MESSAGES/
│       ├── django.po             # Spanish translations
│       └── django.mo             # Compiled binary
├── translator_project/           # Django project settings
│   └── settings.py               # Uses django-environ
├── traductor_app/                # Translation app
│   ├── api_client.py             # funtranslations Livewire client
│   ├── models.py                 # Translation model
│   ├── views.py                  # home, history, details, delete, export
│   ├── services.py               # Translation service + language helpers
│   ├── admin.py                  # Admin configuration
│   └── tests/                    # pytest test modules
│       ├── test_models.py
│       ├── test_views.py
│       ├── test_services.py
│       └── test_api_client.py
├── user_management/              # Auth + profile app
│   ├── views.py                  # login, logout, signin, profile, password
│   ├── urls.py
│   └── tests/
│       └── test_profile.py
├── templates/                    # HTML templates (i18n-enabled)
│   ├── base.html
│   ├── 403.html / 404.html / 500.html
│   ├── registration/             # login, logout, signin, profile, password
│   └── translation/              # home, history, details, results, partials
└── static/                       # CSS, images, favicon
```

## License

This project is for educational purposes.
