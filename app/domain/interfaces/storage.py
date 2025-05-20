"""Storage interfaces for the Video Converter project.

This module defines the core interfaces for file storage operations.
These interfaces follow the Interface Segregation Principle (ISP) by providing
focused interfaces for specific storage operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, BinaryIO


class StorageResult:
    """Result of a storage operation.

    This class encapsulates the result of a storage operation, including
    success status, file key, public URL, and any error information.
    """

    def __init__(
        self,
        success: bool,
        key: Optional[str] = None,
        url: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a storage result.

        Args:
            success (bool): Whether the operation was successful
            key (Optional[str], optional): Storage key for the file. Defaults to None.
            url (Optional[str], optional): Public URL for the file. Defaults to None.
            error (Optional[str], optional): Error message if operation failed. Defaults to None.
            metadata (Optional[Dict[str, Any]], optional): Additional metadata. Defaults to None.
        """
        self.success = success
        self.key = key
        self.url = url
        self.error = error
        self.metadata = metadata or {}

    @classmethod
    def success_result(
        cls, key: str, url: str, metadata: Optional[Dict[str, Any]] = None
    ) -> "StorageResult":
        """Create a successful storage result.

        Args:
            key (str): Storage key for the file
            url (str): Public URL for the file
            metadata (Optional[Dict[str, Any]], optional): Additional metadata. Defaults to None.

        Returns:
            StorageResult: A successful storage result
        """
        return cls(True, key=key, url=url, metadata=metadata)

    @classmethod
    def error_result(
        cls, error: str, metadata: Optional[Dict[str, Any]] = None
    ) -> "StorageResult":
        """Create an error storage result.

        Args:
            error (str): Error message
            metadata (Optional[Dict[str, Any]], optional): Additional metadata. Defaults to None.

        Returns:
            StorageResult: An error storage result
        """
        return cls(False, error=error, metadata=metadata)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the result
        """
        result = {"success": self.success, "metadata": self.metadata}

        if self.key:
            result["key"] = self.key

        if self.url:
            result["url"] = self.url

        if self.error:
            result["error"] = self.error

        return result


class IStorage(ABC):
    """Interface for storage providers.

    This interface defines the contract for all storage providers in the system.
    It follows the Interface Segregation Principle by providing a focused interface
    for storage operations.
    """

    @abstractmethod
    def upload(
        self, file_path: str, content_type: str, custom_key: Optional[str] = None
    ) -> StorageResult:
        """Upload a file to storage.

        Args:
            file_path (str): Path to the file to upload
            content_type (str): MIME type of the file
            custom_key (Optional[str], optional): Custom storage key. Defaults to None.

        Returns:
            StorageResult: Result of the upload operation
        """
        pass

    @abstractmethod
    def upload_stream(
        self, file_stream: BinaryIO, content_type: str, custom_key: str
    ) -> StorageResult:
        """Upload a file stream to storage.

        Args:
            file_stream (BinaryIO): File stream to upload
            content_type (str): MIME type of the file
            custom_key (str): Storage key for the file

        Returns:
            StorageResult: Result of the upload operation
        """
        pass

    @abstractmethod
    def download(self, key: str, destination: str) -> StorageResult:
        """Download a file from storage.

        Args:
            key (str): Storage key of the file to download
            destination (str): Path to save the downloaded file

        Returns:
            StorageResult: Result of the download operation
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a file from storage.

        Args:
            key (str): Storage key of the file to delete

        Returns:
            bool: True if the file was deleted, False otherwise
        """
        pass

    @abstractmethod
    def get_public_url(self, key: str) -> str:
        """Get the public URL for a file.

        Args:
            key (str): Storage key of the file

        Returns:
            str: Public URL for the file
        """
        pass
