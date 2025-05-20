"""Base abstract classes for storage providers in the Video Converter project.

This module provides base implementations of the storage interfaces
defined in app.domain.interfaces.storage. These abstract classes implement
common functionality while leaving specific storage logic to concrete subclasses.
"""

from abc import ABC, abstractmethod
from typing import Optional, BinaryIO
import os
import logging
import mimetypes
from pathlib import Path

from app.domain.interfaces.storage import IStorage, StorageResult


logger = logging.getLogger(__name__)


class BaseStorage(IStorage, ABC):
    """Base abstract class for storage providers.

    This class provides a common implementation for the IStorage interface,
    including file validation and result handling.
    """

    def upload(
        self,
        file_path: str,
        content_type: Optional[str] = None,
        custom_key: Optional[str] = None,
    ) -> StorageResult:
        """Upload a file to storage.

        Args:
            file_path (str): Path to the file to upload
            content_type (str, optional): MIME type of the file. Defaults to None (auto-detected).
            custom_key (Optional[str], optional): Custom storage key. Defaults to None.

        Returns:
            StorageResult: Result of the upload operation
        """
        # Validate file
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            return StorageResult.error_result(f"File does not exist: {file_path}")

        if not os.path.isfile(file_path):
            logger.error(f"Path is not a file: {file_path}")
            return StorageResult.error_result(f"Path is not a file: {file_path}")

        if not os.access(file_path, os.R_OK):
            logger.error(f"File is not readable: {file_path}")
            return StorageResult.error_result(f"File is not readable: {file_path}")

        # Auto-detect content type if not provided
        if content_type is None:
            content_type = self._get_content_type(file_path)

        # Generate key if not provided
        key = custom_key or self._generate_key(file_path)

        try:
            # Open file and upload using stream method
            with open(file_path, "rb") as file_stream:
                return self.upload_stream(file_stream, content_type, key)
        except Exception as e:
            logger.exception(f"Error uploading file: {str(e)}")
            return StorageResult.error_result(f"Upload failed: {str(e)}")

    def download(self, key: str, destination: str) -> StorageResult:
        """Download a file from storage.

        Args:
            key (str): Storage key of the file to download
            destination (str): Path to save the downloaded file

        Returns:
            StorageResult: Result of the download operation
        """
        # Ensure destination directory exists
        destination_dir = os.path.dirname(destination)
        if destination_dir:
            try:
                os.makedirs(destination_dir, exist_ok=True)
            except Exception as e:
                logger.error(
                    f"Failed to create destination directory: {destination_dir}. Error: {str(e)}"
                )
                return StorageResult.error_result(
                    f"Failed to create destination directory: {str(e)}"
                )

        try:
            # Perform the actual download (implemented by subclasses)
            return self._perform_download(key, destination)
        except Exception as e:
            logger.exception(f"Error downloading file: {str(e)}")
            return StorageResult.error_result(f"Download failed: {str(e)}")

    def _get_content_type(self, file_path: str) -> str:
        """Get the content type (MIME type) of a file.

        Args:
            file_path (str): Path to the file

        Returns:
            str: MIME type of the file
        """
        content_type, _ = mimetypes.guess_type(file_path)
        return content_type or "application/octet-stream"

    def _generate_key(self, file_path: str) -> str:
        """Generate a storage key for a file.

        Args:
            file_path (str): Path to the file

        Returns:
            str: Generated storage key
        """
        # Use the filename as the key by default
        return Path(file_path).name

    @abstractmethod
    def upload_stream(
        self, file_stream: BinaryIO, content_type: str, custom_key: str
    ) -> StorageResult:
        """Upload a file stream to storage.

        This method should be implemented by subclasses to perform the
        specific upload logic.

        Args:
            file_stream (BinaryIO): File stream to upload
            content_type (str): MIME type of the file
            custom_key (str): Storage key for the file

        Returns:
            StorageResult: Result of the upload operation
        """
        pass

    @abstractmethod
    def _perform_download(self, key: str, destination: str) -> StorageResult:
        """Perform the actual file download.

        This method should be implemented by subclasses to perform the
        specific download logic.

        Args:
            key (str): Storage key of the file to download
            destination (str): Path to save the downloaded file

        Returns:
            StorageResult: Result of the download operation
        """
        pass
