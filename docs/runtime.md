# Runtime Guide

This file shows the exact runtime sequence to launch the application after dependency installation.

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Create environment file

Linux/macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

## 3. (Optional but recommended) run migrations manually

If `alembic` is available in your environment:

```bash
alembic upgrade head
```

Note: the app also runs `alembic upgrade head` automatically on startup.

## 4. Run application

```bash
python main.py
```

## 5. Verify runtime

Open:

```text
http://127.0.0.1:8000/
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## Full quick run (Linux/macOS)

```bash
pip install -r requirements.txt
cp .env.example .env
python main.py
```
back to <a href="../readme.md">README.md</a>