import uvicorn
from src.core.settings import Application as app
from src.utils.logging import color, configure_logging, get_logger

def main():
    configure_logging()
    app_logger = get_logger()
    app_url = f"http://{app.host}:{app.port}"
    colored_url = color(app_url, tc='#93c5fd', bc='#000')
    try:
        app_logger.opt(colors=True).success(
            f"Starting application on {colored_url}", extra={"module": "main"}
        )
        uvicorn.run(
            "src.app:app",
            host=app.host,
            port=app.port,
            reload=app.debug_mode,
            log_config=None,
        )
    except Exception as exc:
        app_logger.error(
            "Error starting application",
            extra={"module": "main", "error": str(exc)}
        )
        raise

if __name__ == "__main__":
    main()