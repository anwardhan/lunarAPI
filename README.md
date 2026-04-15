# Lunar Car API

Phase 1 FastAPI backend for Lunar Car.

## Local setup

### Option A: no Docker, SQLite local dev

Use this if Docker Desktop is not installed yet. This is enough to run the API locally and exercise the iOS app contract.

```bash
cd "/Users/anwardhanani/Developer/LunarCar/LunarCar API"
chmod +x scripts/run_sqlite_dev.sh
scripts/run_sqlite_dev.sh
```

The script refuses Python older than 3.11 and prefers `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3` when it is available. If pyenv is forcing Python 3.7, you can also run the commands manually with an explicit interpreter:

```bash
PY="/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"
$PY -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[test]"
cp .env.sqlite.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Use `.venv/bin/python -m uvicorn` or activate the venv first; do not use bare `uvicorn` from pyenv Python 3.7. This project requires Python 3.11+.

### Option B: Postgres/PostGIS with Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
cp .env.example .env
docker compose up -d postgres redis
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API listens on port `8000` by default. Use `--host 0.0.0.0` when testing from a physical iPhone so the app can reach the Mac over Wi-Fi, for example `http://192.168.1.70:8000`. Use `--host 127.0.0.1` if you only want the API reachable from the Mac.

If `docker compose` prints `command not found`, install Docker Desktop or use the SQLite path above.

## Environment

- `DATABASE_URL`: SQLAlchemy async database URL. Local default uses Postgres/PostGIS.
- `JWT_SECRET`: signing secret for Lunar access and refresh JWTs.
- `AUTH_PROVIDER_VERIFICATION`: `development` accepts any non-empty provider token and creates a stable dev identity. Production must replace this with real Apple and Google token verification.
- `LOCAL_UPLOAD_ROOT`: directory used by the local presigned-upload placeholder.
- `STORAGE_BUCKET`: logical bucket name stored on media records.

## Implemented Phase 1 routes

Versioned routes are primary. Compatibility aliases are also exposed for the simple Phase 1 contract.

- `POST /v1/auth/apple/login` and `POST /auth/apple`
- `POST /v1/auth/google/login` and `POST /auth/google`
- `POST /v1/auth/refresh` and `POST /auth/refresh`
- `GET /v1/me` and `GET /me`
- `POST /v1/trips/start` and `POST /trips/start`
- `POST /v1/trips/{trip_id}/points` and `POST /trips/{trip_id}/points`
- `POST /v1/trips/{trip_id}/end` and `POST /trips/{trip_id}/end`
- `POST /v1/media/upload-url` and `POST /media/upload-url`
- `POST /v1/submissions/sticker` and `POST /sticker-verifications`
- `POST /v1/submissions/odometer` and `POST /odometer-submissions`

## Running tests

```bash
pytest
```

Tests use an async SQLite database and exercise auth, trip ingestion, trip end, and both submission flows.

## Integration placeholders

Apple and Google token verification are isolated behind `AuthService.verify_provider_token`. In `development` mode the backend accepts any non-empty token and derives a stable provider subject for local testing. Production must implement real provider verification and configure Apple/Google client IDs.

`MediaService` returns a local dev upload URL when object storage credentials are not configured. The URL accepts `PUT` requests under `/v1/media/dev-upload/{object_key}` and writes files to `LOCAL_UPLOAD_ROOT`. Replace this path with S3/DigitalOcean Spaces presigning before production.
# lunarAPI
# lunarAPI
