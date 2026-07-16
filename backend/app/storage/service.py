"""Local filesystem storage service."""

import hashlib
import uuid
from pathlib import Path

from app.storage.exceptions import StorageDeleteError, StorageWriteError


class StorageService:
    """Filesystem adapter for saving and deleting uploaded files.

    All paths returned by this service are relative to `upload_directory` so
    that the storage root can be changed (or replaced with S3) without touching
    the Documents module.
    """

    def __init__(self, upload_directory: str) -> None:
        self._root = Path(upload_directory)
        # Ensure the root upload directory exists at service construction time
        self._root.mkdir(parents=True, exist_ok=True)

    def save_file(
        self,
        file_data: bytes,
        workspace_id: uuid.UUID,
        original_filename: str,
    ) -> str:
        """Persist bytes to disk and return the relative storage path."""
        workspace_dir = self._root / str(workspace_id)
        workspace_dir.mkdir(parents=True, exist_ok=True)

        extension = Path(original_filename).suffix.lower()
        stored_filename = f"{uuid.uuid4()}{extension}"
        absolute_path = workspace_dir / stored_filename
        # Relative path gets persisted to disk
        relative_path = str(Path(str(workspace_id)) / stored_filename)

        try:
            absolute_path.write_bytes(file_data)
        except OSError as exc:
            raise StorageWriteError(path=relative_path, reason=str(exc)) from exc

        return relative_path

    def delete_file(self, storage_path: str) -> None:
        """Remove the file at the given relative storage path."""
        absolute_path = self._root / storage_path
        try:
            absolute_path.unlink()
        except OSError as exc:
            raise StorageDeleteError(path=storage_path, reason=str(exc)) from exc

    def file_exists(self, storage_path: str) -> bool:
        """Return True if the file exists at the given relative storage path."""
        return (self._root / storage_path).is_file()

    def generate_checksum(self, file_data: bytes) -> str:
        """Return the SHA-256 hex digest of the given bytes."""
        return hashlib.sha256(file_data).hexdigest()
