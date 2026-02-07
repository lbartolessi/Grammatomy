import gzip
import logging
import logging.config
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter to add ANSI colors to console logs.
    """

    grey = "\x1b[38;20m"
    green = "\x1b[32;20m"
    orange = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_str = "%(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: green + format_str + reset,
        logging.WARNING: orange + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class CompressedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    A RotatingFileHandler that compresses rotated logs with gzip.
    It inherits from the standard class and overrides the rotation hooks.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.namer = self._namer
        self.rotator = self._rotator

    @staticmethod
    def _namer(name: str) -> str:
        """Adds the .gz extension to the rotated file name."""
        return name + ".gz"

    @staticmethod
    def _rotator(source: str, dest: str) -> None:
        """Compresses the source log file to the destination file using gzip."""
        with open(source, "rb") as f_in:
            with gzip.open(dest, "wb") as f_out:
                f_out.writelines(f_in)
        os.remove(source)


def setup_logging(
    name: str = "grammatomy",
    log_file: Optional[Path] = None,
    console_level: int = logging.INFO,
    file_level: int = logging.WARNING,
    rotate: bool = True,
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 3,
) -> logging.Logger:
    """
    Sets up the application logger with console and rotating file support.

    Args:
        name: Name of the logger.
        log_file: Path to the log file. If None, only logs to console.
        console_level: Level for standard output (default: INFO).
        file_level: Level for the log file (default: WARNING).
        rotate: If True, use RotatingFileHandler to limit file size.
        max_bytes: Maximum file size before rotating.
        backup_count: Number of backup files to keep.
    """
    logger = logging.getLogger(name)
    # The base logger must capture the lowest level of its handlers
    logger.setLevel(min(console_level, file_level))

    # Avoid duplicating handlers on multiple calls (e.g., Streamlit reruns)
    if logger.hasHandlers():
        return logger

    # 1. Console Handler (with colors)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter("%(levelname)s - %(message)s"))
    console_handler.setLevel(console_level)
    logger.addHandler(console_handler)

    # 2. File Handler (optional, with rotation)
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            if rotate:
                file_handler = CompressedRotatingFileHandler(
                    log_path,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding="utf-8",
                )
            else:
                file_handler = logging.FileHandler(log_path, encoding="utf-8")

            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(file_level)
            logger.addHandler(file_handler)
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Fallback to console if filesystem fails (e.g., permissions on HFS)
            logger.error("Failed to setup file logging: %s", e)

    # Do not propagate to root to avoid duplicate logs from libraries
    logger.propagate = False

    return logger
