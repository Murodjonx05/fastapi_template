# FastAPI Template

Minimal FastAPI starter with SQLAlchemy, SQLite, SlowAPI, and custom Loguru logging.

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

See [.env.example](/home/aestra/Рабочий стол/course_sqlalchemy/.env.example).

- `HOST`, `PORT`, `RELOAD`
- `DATABASE_URL`
- `LOG_LEVEL`, `SQLALCHEMY_LOG_LEVEL`, `LOG_ENQUEUE`
- `NAME`, `DESCRIPTION`, `VERSION`

## Includes

- async SQLAlchemy setup
- automatic SQLite database creation
- rate limiting with JSON responses
- unified custom logging
- retry and profiling utilities

## Structure

```text
main.py
src/
data/
```
