import uvicorn
from src.core.settings import app_settings as app
from src.utils.logging import color, configure_logging, get_logger

def main():
    configure_logging()
    log = get_logger()
    url = color(f"http://{app.host}:{app.port}", tc='#93c5fd', bc='#000')
    try:
        log.opt(colors=True).success(f"Starting application on {url}", extra={"module": "main"})
        uvicorn.run("src.app:app", host=app.host, port=app.port, reload=app.debug_mode, log_config=None)
    except Exception as e:
        log.error("Error starting application", extra={"module": "main", "error": str(e)})
        raise

if __name__ == "__main__":
    main()