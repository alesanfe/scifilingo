# SciFiLingo

A Django web application that translates text into fictional languages (Yoda, Klingon, Sith, Dothraki, Quenya, and more) using the [funtranslations.com](https://funtranslations.com/api) public API. Users can sign up, translate text, and browse their translation history.

## Features

- Translate text into 15+ fictional languages
- User authentication (sign up, login, logout)
- Per-user translation history with detail views
- Admin interface for managing translations
- Responsive UI with Bootstrap 4.6
- Secure by default (HSTS, SSL redirect, secure cookies, CSRF protection)
- Deploy-ready for Render (PostgreSQL + WhiteNoise + Gunicorn)
- CI/CD with GitHub Actions (linting, tests, deploy checks, auto-deploy)

## Tech Stack

- Python 3.11 / Django 4.2
- django-environ for environment variable management
- SQLite (development) / PostgreSQL (production)
- funtranslations.com API
- Bootstrap 4.6
- WhiteNoise for static files
- Gunicorn as WSGI server
- Ruff for linting and formatting
- pytest + pytest-django for testing

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
| `FUNTRANSLATIONS_API_KEY` | No | empty | Optional API key for higher rate limits (paid plan). |
| `RENDER_EXTERNAL_HOSTNAME` | Auto | empty | Set automatically by Render. |
| `DATABASE_URL` | Production | SQLite | PostgreSQL connection string. Auto-set on Render. |

## API: funtranslations.com

The app uses the funtranslations.com translation API:

- **Endpoint**: `POST https://api.funtranslations.com/translate/{language}.json`
- **Body**: `{"text": "..."}`
- **Auth**: Optional `X-FunTranslations-Api-Secret` header (paid plans)
- **Free tier limits**: 60 calls/day, 5 calls/hour
- **Paid plans**: 1,000–12,500 calls/day

Rate limit errors (HTTP 429) are handled gracefully and shown to the user via flash messages.

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

# Verify formatting
ruff format --check .
```

### Django Checks

```bash
# System checks
python manage.py check

# Production deployment checks
python manage.py check --deploy

# Verify migrations are up to date
python manage.py makemigrations --check --dry-run
```

## Deployment

### Render (recommended)

1. Fork/push this repo to GitHub.
2. Go to [Render](https://render.com) and create a new Web Service from the repo.
3. The included `render.yaml` defines the service and a PostgreSQL database.
4. Set the `FUNTRANSLATIONS_API_KEY` env var if you have a paid plan.
5. Render runs `build.sh` (collectstatic + migrate) and starts Gunicorn automatically.

### GitHub Actions

Two workflows are included in `.github/workflows/`:

- **`ci.yml`**: Runs on every push/PR to `main`/`master`.
  - **Lint job**: Ruff check + format check
  - **Test job**: Django system checks, deploy checks, migration consistency, collectstatic, pytest
- **`deploy.yml`**: Triggers on push to `main`. Calls the Render deploy hook URL stored in the `RENDER_DEPLOY_HOOK_URL` repository secret.

To enable the deploy workflow:
1. In Render, go to your service → Settings → Deploy Hook → create a hook URL.
2. In GitHub, go to repo → Settings → Secrets and variables → Actions → add `RENDER_DEPLOY_HOOK_URL` with the hook URL.

## Project Structure

```
scifilingo/
├── manage.py
├── build.sh                      # Build script for Render
├── render.yaml                   # Render service definition
├── pyproject.toml                # Ruff + pytest config
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Dev dependencies (lint + test)
├── .env.example                  # Example environment variables
├── .github/workflows/
│   ├── ci.yml                    # CI: lint + checks + tests
│   └── deploy.yml                # CD: trigger Render deploy
├── translator_project/           # Django project settings
│   └── settings.py               # Uses django-environ
├── traductor_app/                # Translation app
│   ├── api_client.py             # funtranslations API client
│   ├── models.py                 # Translation model
│   ├── views.py                  # home, history, details
│   ├── admin.py                  # Admin configuration
│   └── tests/                    # pytest test modules
│       ├── test_models.py
│       ├── test_views.py
│       └── test_api_client.py
├── user_management/              # Auth app (login, logout, signin)
├── templates/                    # HTML templates
└── static/                       # CSS, images
```

## License

This project is for educational purposes.
