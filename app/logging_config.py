import logging
import logging.handlers
import os
from pathlib import Path

LOG_DIR = Path(os.getenv("LOG_DIR", Path(__file__).resolve().parent / "logs"))
LOG_FILE_NAME = os.getenv("LOG_FILE_NAME", "music_service.log")


def configure_logging(level: str | None = None, path: Path | None = None) -> None:
    """Настраивает логгирование: консоль + файл с ротацией.

    Уровень берётся из переданного аргумента или переменной окружения LOG_LEVEL
    (DEBUG / INFO / WARNING / ERROR), по умолчанию INFO. Уровень файла всегда DEBUG.
    """
    root = logging.getLogger()

    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    num_level = getattr(logging, (level or os.getenv("LOG_LEVEL", "INFO")).upper(), logging.INFO)
    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setLevel(num_level)
    console.setFormatter(formatter)
    root.addHandler(console)

    log_path = Path(path or (LOG_DIR / LOG_FILE_NAME))
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)