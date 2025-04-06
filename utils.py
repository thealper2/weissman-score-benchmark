import os
import sys
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, validator
import tempfile


class InputPathModel(BaseModel):
    """Pydantic model for validating input paths."""

    path: Path

    @validator("path")
    def path_must_exist(cls, v):
        """Validate that the path exists."""
        if not v.exists():
            raise ValueError(f"Path does not exist: {v}")
        return v

    @property
    def is_file(self) -> bool:
        """Check if the path is a file."""
        return self.path.is_file()

    @property
    def is_dir(self) -> bool:
        """Check if the path is a directory."""
        return self.path.is_dir()


def validate_input_path(path_str: str) -> Optional[Path]:
    """
    Validate that the input path exists and is a file or directory.

    Args:
        path_str (str): Input path as a string

    Returns:
        Optional[Path]: Path object if valid, None otherwise
    """
    try:
        path = Path(path_str).resolve()
        InputPathModel(path=path)
        return path
    except (ValueError, Exception) as e:
        logging.error(f"Invalid path: {e}")
        return None


def setup_logger(verbose: bool = False) -> logging.Logger:
    """
    Set up and configure logger.

    Args:
        verbose (bool): Whether to enable verbose logging

    Returns:
        logging.Logger: Configured logger
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    logger = logging.getLogger("compression_benchmark")
    logger.setLevel(log_level)

    # Clear existing handlers
    logger.handlers = []

    # Create console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    return logger


def secure_temp_file() -> Path:
    """
    Create a secure temporary file with appropriate permissions.

    Returns:
        Path: Path to the secure temporary file
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_path = Path(temp_file.name)

    # Set secure permissions (read/write only for the owner)
    os.chmod(temp_path, 0o600)

    return temp_path


def secure_delete(path: Path) -> None:
    """
    Securely delete a file by overwriting it with zeros before unlinking.

    Args:
        path (Path): Path to the file to delete
    """
    if path.exists() and path.is_file():
        try:
            # Get file size
            file_size = path.stat().st_size

            # Overwrite with zeros
            with open(path, "wb") as f:
                f.write(b"\x00" * file_size)
                f.flush()
                os.fsync(f.fileno())

            # Delete the file
            os.unlink(path)
        except Exception as e:
            logging.error(f"Error securely deleting {path}: {e}")
            # Fallback to regular delete
            try:
                os.unlink(path)
            except Exception:
                pass
