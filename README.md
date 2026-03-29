# FastAPI Template

Minimal FastAPI starter with SQLAlchemy, SQLite, SlowAPI, and custom Loguru logging.

Detailed runtime steps: [runtime.md](./docs/runtime.md)

## Quick Start

### Option 1: Python venv

1. Create a virtual environment.

```bash
python -m venv venv
```

2. Activate it.

Linux/macOS:

```bash
source venv/bin/activate
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Windows CMD:

```bat
venv\Scripts\activate.bat
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Create `.env`.

Linux/macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Windows CMD:

```bat
copy .env.example .env
```

5. Run the app.

```bash
python main.py
```

### Option 2: uv

1. Install `uv`.

Debian/Ubuntu:

```bash
sudo apt-get install uv
```

Arch-based Linux:

```bash
sudo pacman -S uv
```

Any platform with Python:

```bash
pip install uv
```

2. Create a virtual environment.

```bash
uv venv venv
```

3. Activate it.

Linux/macOS:

```bash
source venv/bin/activate
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Windows CMD:

```bat
venv\Scripts\activate.bat
```

4. Install dependencies.

```bash
uv pip install -r requirements.txt
```

5. Create `.env`.

Linux/macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Windows CMD:

```bat
copy .env.example .env
```

6. Run the app.

```bash
python main.py
```

Default app URL: `http://127.0.0.1:8000`

## Environment

See [.env.example](./.env.example).

- `HOST`, `PORT`, `RELOAD`
- `DATABASE_URL`
- `DB_REQUIRE_TLS`: keep this `True` for production and remote PostgreSQL deployments so database connections are encrypted
- `LOG_LEVEL`, `SQLALCHEMY_LOG_LEVEL`, `LOG_ENQUEUE`
- `NAME`, `DESCRIPTION`, `VERSION`

## Includes

- async SQLAlchemy setup
- automatic SQLite database directory creation
- automatic Alembic migration on app startup
- rate limiting with JSON responses
- unified custom logging
- retry and profiling utilities

## Database Migrations (Best Practice)

This project uses **Alembic as the single source of truth** for schema changes.
The app applies migrations automatically on startup via lifespan hook.

- Startup flow: `alembic upgrade head`
- No runtime `Base.metadata.create_all(...)` fallback is used.

### Manual migration commands

Apply latest migrations:

```bash
alembic upgrade head
```

Create a new migration:

```bash
alembic revision -m "your message"
```

Rollback one revision:

```bash
alembic downgrade -1
```

## Structure

```text
main.py
src/
data/
```
## How to Run the Project

For step-by-step instructions, see [runtime.md](./docs/runtime.md).
