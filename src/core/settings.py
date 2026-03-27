import os
from pathlib import Path

from dotenv import load_dotenv

base_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(base_dir / ".env")

default_db_path = (base_dir / "data" / "database.db").resolve()

class Product:
    title: str = os.getenv("NAME", "FastAPI Application")
    description: str = os.getenv("DESCRIPTION", "FastAPI Application")
    version:str = os.getenv("VERSION", "1.0.0")

class Database:
    database_url: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{default_db_path.as_posix()}")

class Application(Product, Database):
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))
    debug_mode: bool = os.getenv("RELOAD", "False").lower() in ("true", "1", "yes")
