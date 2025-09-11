import logging
import sys

def init_app_logging(log_level=logging.INFO):
    """
    Initialize application-wide logging with a consistent format.
    Logs to both console (stdout) and optionally to a file if needed.
    """
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Uncomment below to enable file logging
    # file_handler = logging.FileHandler('app.log')
    # file_handler.setFormatter(formatter)
    # root_logger.addHandler(file_handler)

    # Reduce verbosity of some noisy loggers (optional)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
