"""
Storage abstraction layer for local filesystem (with S3-ready interface).
"""

import shutil
from pathlib import Path
from typing import Optional, BinaryIO
import logging


logger = logging.getLogger(__name__)


class StorageBackend:
    """Base class for storage backends."""

    def put_bytes(self, path: str, data: bytes) -> bool:
        """Store bytes at path."""
        raise NotImplementedError

    def get_bytes(self, path: str) -> Optional[bytes]:
        """Retrieve bytes from path."""
        raise NotImplementedError

    def exists(self, path: str) -> bool:
        """Check if path exists."""
        raise NotImplementedError

    def open(self, path: str, mode: str = 'rb') -> BinaryIO:
        """Open file at path."""
        raise NotImplementedError

    def delete(self, path: str) -> bool:
        """Delete file at path."""
        raise NotImplementedError


class LocalStorage(StorageBackend):
    """
    Local filesystem storage backend.

    Default storage for the federal ingestion system.
    """

    def __init__(self, base_path: str = "./federal_data"):
        """
        Initialize local storage.

        Args:
            base_path: Base directory for all stored files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized local storage at {self.base_path}")

    def _resolve_path(self, path: str) -> Path:
        """Resolve relative path to absolute path within base_path."""
        full_path = self.base_path / path
        # Ensure path is within base_path (security check)
        if not str(full_path.resolve()).startswith(str(self.base_path.resolve())):
            raise ValueError(f"Path {path} is outside base directory")
        return full_path

    def put_bytes(self, path: str, data: bytes) -> bool:
        """Store bytes at path."""
        try:
            full_path = self._resolve_path(path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'wb') as f:
                f.write(data)
            logger.debug(f"Stored {len(data)} bytes to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to store to {path}: {e}")
            return False

    def get_bytes(self, path: str) -> Optional[bytes]:
        """Retrieve bytes from path."""
        try:
            full_path = self._resolve_path(path)
            if not full_path.exists():
                return None
            with open(full_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to retrieve {path}: {e}")
            return None

    def exists(self, path: str) -> bool:
        """Check if path exists."""
        try:
            full_path = self._resolve_path(path)
            return full_path.exists()
        except Exception:
            return False

    def open(self, path: str, mode: str = 'rb') -> BinaryIO:
        """Open file at path."""
        full_path = self._resolve_path(path)
        return open(full_path, mode)

    def delete(self, path: str) -> bool:
        """Delete file at path."""
        try:
            full_path = self._resolve_path(path)
            if full_path.exists():
                full_path.unlink()
                logger.debug(f"Deleted {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete {path}: {e}")
            return False

    def copy(self, src_path: str, dest_path: str) -> bool:
        """Copy file from src to dest."""
        try:
            src_full = self._resolve_path(src_path)
            dest_full = self._resolve_path(dest_path)
            dest_full.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_full, dest_full)
            logger.debug(f"Copied {src_path} to {dest_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy {src_path} to {dest_path}: {e}")
            return False


# TODO: S3Storage backend for cloud deployment
class S3Storage(StorageBackend):
    """
    S3 storage backend (placeholder for future implementation).
    """

    def __init__(self, bucket: str, prefix: str = ""):
        self.bucket = bucket
        self.prefix = prefix
        raise NotImplementedError("S3Storage not yet implemented")

    def put_bytes(self, path: str, data: bytes) -> bool:
        raise NotImplementedError

    def get_bytes(self, path: str) -> Optional[bytes]:
        raise NotImplementedError

    def exists(self, path: str) -> bool:
        raise NotImplementedError

    def open(self, path: str, mode: str = 'rb') -> BinaryIO:
        raise NotImplementedError

    def delete(self, path: str) -> bool:
        raise NotImplementedError


# Default storage instance
_default_storage: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    """Get the default storage backend."""
    global _default_storage
    if _default_storage is None:
        _default_storage = LocalStorage()
    return _default_storage


def set_storage(storage: StorageBackend):
    """Set the default storage backend."""
    global _default_storage
    _default_storage = storage
