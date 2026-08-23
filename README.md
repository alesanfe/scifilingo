# SciFiLingo

A Django web application that translates text into fictional languages (Yoda, Klingon, Sith, Dothraki, Quenya, and more) using the [funtranslations.com](https://funtranslations.com/api) public API. Users can sign up, translate text, and browse their translation history.

## Features

- Translate text into 15+ fictional languages
- User authentication (sign up, login, logout)
- Per-user translation history with detail views
- Admin interface for managing translations
- Responsive UI with Bootstrap 4
- Deploy-ready for Render (PostgreSQL + WhiteNoise + Gunicorn)

## Tech Stack

- Python 3.11 / Django 4.2
- SQLite (development) / PostgreSQL (production)
- funtranslations.com API
- Bootstrap 4.6
- WhiteNoise for static files
- Gunicorn as WSGI server

## Setup

```bash
# Clone the repo
git clone https://github.com/alesanfe/scifilingo.git
cd scifilingo

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create a superuser (optional, for admin access)
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

Visit http://127.0.0.1:8000/translation/ to use the app.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Production | Django secret key. A random one is generated on Render. |
| `FUNTRANSLATIONS_API_KEY` | No | Optional API key for higher rate limits (paid plan). Free tier works without it. |
| `RENDER_EXTERNAL_HOSTNAME` | Auto | Set automatically by Render. |
| `DATABASE_URL` | Production | PostgreSQL connection string. Set automatically by Render. |

## API: funtranslations.com

The app uses the funtranslations.com translation API:

- **Endpoint**: `POST https://api.funtranslations.com/translate/{language}.json`
- **Body**: `{"text": "..."}`
- **Auth**: Optional `X-FunTranslations-Api-Secret` header (paid plans)
- **Free tier limits**: 60 calls/day, 5 calls/hour
- **Paid plans**: 1,000–12,500 calls/day

Rate limit errors (HTTP 429) are handled gracefully and shown to the user via flash messages.

## Deployment

### Render (recommended)

1. Fork/push this repo to GitHub.
2. Go to [Render](https://render.com) and create a new Web Service from the repo.
3. The included `render.yaml` defines the service and a PostgreSQL database.
4. Set the `FUNTRANSLATIONS_API_KEY` env var if you have a paid plan.
5. Render runs `build.sh` (collectstatic + migrate) and starts Gunicorn automatically.

### GitHub Actions

Two workflows are included in `.github/workflows/`:

- **`ci.yml`**: Runs on every push/PR to `main`/`master`. Performs Django system checks, migration consistency checks, collectstatic, and tests.
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
├── requirements.txt
├── .github/workflows/
│   ├── ci.yml                    # CI: checks + tests
│   └── deploy.yml                # CD: trigger Render deploy
├── translator_project/           # Django project settings
├── traductor_app/                # Translation app
│   ├── api_client.py             # funtranslations API client
│   ├── models.py                 # Translation model
│   ├── views.py                  # home, history, details
│   └── tests.py
├── user_management/              # Auth app (login, logout, signin)
├── templates/                    # HTML templates
└── static/                       # CSS, images
```

## License

This project is for educational purposes.
