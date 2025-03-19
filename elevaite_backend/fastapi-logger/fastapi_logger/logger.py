import logging
import sys


class FastAPILogger:
    def __init__(
        self,
        name: str = "fastapi_logger",
        level: int = logging.DEBUG,
        stream=sys.stdout,
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Prevent duplicate handlers if already configured
        if not self.logger.handlers:
            handler = logging.StreamHandler(stream)
            formatter = logging.Formatter(
                "[elevAIte Logger] %(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def get_logger(self):
        return self.logger

    @staticmethod
    def attach_to_uvicorn():
        """Attach this logger to Uvicorn and FastAPI logs."""
        custom_logger = FastAPILogger().get_logger()

        # Redirect Uvicorn logs
        for uvicorn_logger in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
            logging.getLogger(uvicorn_logger).handlers = custom_logger.handlers
            logging.getLogger(uvicorn_logger).setLevel(logging.DEBUG)

        # Redirect FastAPI logs
        logging.getLogger("fastapi").handlers = custom_logger.handlers
        logging.getLogger("fastapi").setLevel(logging.DEBUG)
