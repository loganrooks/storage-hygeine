import pathlib
import os
import hashlib
from datetime import datetime, timezone
from .config_manager import ConfigManager
from .metadata_store import MetadataStore


class Scanner:
    """
    Scans directories for files, collects metadata, calculates hashes,
    and interacts with the MetadataStore.
    """
    def __init__(self, config_manager: ConfigManager, metadata_store: MetadataStore):
        """
        Initializes the Scanner with dependencies.

        Args:
            config_manager: An instance of ConfigManager.
            metadata_store: An instance of MetadataStore.
        """
        self.config_manager = config_manager
        self.metadata_store = metadata_store
        self._hash_chunk_size = 65536 # 64kb chunk size for hashing

    def _calculate_hash(self, file_path: pathlib.Path) -> str | None:
        """Calculates the SHA-256 hash of a file, reading in chunks."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as file:
                while chunk := file.read(self._hash_chunk_size):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except OSError as e:
            print(f"Error calculating hash for {file_path}: {e}")
            return None

    def scan_directory(self, directory_path: str):
        """
        Recursively scans a directory, identifies files, and triggers processing.

        Args:
            directory_path: The absolute path to the directory to scan.
        """
        root_path = pathlib.Path(directory_path)
        if not root_path.is_dir():
            # Handle error: path is not a directory or doesn't exist
            # For now, just return or log, proper error handling later
            print(f"Error: Path is not a valid directory: {directory_path}")
            return

        # Define a small tolerance for timestamp comparisons (e.g., 1 second)
        # due to potential floating point inaccuracies or filesystem differences
        TIMESTAMP_TOLERANCE_SECONDS = 1 # Define tolerance at class level or pass via config? For now, keep here.

    def _process_file(self, item_path: pathlib.Path):
        """Processes a single file: checks incremental, collects metadata, hashes, upserts."""
        TIMESTAMP_TOLERANCE_SECONDS = 1 # Re-define here for now, consider class level later
        try:
            resolved_path = item_path.resolve()
            # Collect basic metadata
            stat_result = item_path.stat()
            size = stat_result.st_size
            mtime_ts = stat_result.st_mtime
            # Convert mtime to timezone-aware UTC datetime
            last_modified = datetime.fromtimestamp(mtime_ts, tz=timezone.utc)

            # Check metadata store for existing record (Incremental Scan Logic)
            existing_records = self.metadata_store.query_files(path=resolved_path)
            existing_record = existing_records[0] if existing_records else None

            # Compare metadata if record exists
            if existing_record:
                stored_last_modified = existing_record.get('last_modified')
                stored_size = existing_record.get('size')

                # Check if size and mtime match (within tolerance)
                if stored_size == size and stored_last_modified and \
                   abs((last_modified - stored_last_modified).total_seconds()) < TIMESTAMP_TOLERANCE_SECONDS:
                    # Metadata matches, skip hashing and upsert
                    print(f"Skipping unchanged file: {resolved_path}")
                    return # Skip processing this file

            # If no record or metadata mismatch, proceed with hashing and upsert
            hash_value = self._calculate_hash(item_path)

            # Call upsert with collected metadata and hash
            self.metadata_store.upsert_file_record(
                file_path=resolved_path,
                size=size,
                last_modified=last_modified,
                hash_value=hash_value
            )
        except OSError as e:
            # Handle potential errors during stat() or hashing
            print(f"Error processing file {item_path}: {e}")

    def scan_directory(self, directory_path: str):
        """
        Recursively scans a directory, identifies files, and triggers processing for each.

        Args:
            directory_path: The absolute path to the directory to scan.
        """
        root_path = pathlib.Path(directory_path)
        if not root_path.is_dir():
            print(f"Error: Path is not a valid directory: {directory_path}")
            return

        for item_path in root_path.rglob('*'):
            if item_path.is_file():
                self._process_file(item_path)