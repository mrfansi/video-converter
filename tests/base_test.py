"""Base test class for the Video Converter project."""

import os
import pytest
import logging
from pathlib import Path

class BaseTest:
    """Base test class with common utilities for all tests."""
    
    @classmethod
    def setup_class(cls):
        """Set up test class."""
        # Configure logging for tests
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        cls.logger = logging.getLogger(cls.__name__)
        cls.logger.info(f"Setting up {cls.__name__}")
        
        # Create test data directory if it doesn't exist
        cls.test_data_dir = Path(__file__).parent / "data"
        cls.test_data_dir.mkdir(exist_ok=True)
    
    @classmethod
    def teardown_class(cls):
        """Tear down test class."""
        cls.logger.info(f"Tearing down {cls.__name__}")
    
    def setup_method(self, method):
        """Set up test method."""
        self.logger.info(f"Setting up {method.__name__}")
    
    def teardown_method(self, method):
        """Tear down test method."""
        self.logger.info(f"Tearing down {method.__name__}")
    
    @staticmethod
    def assert_file_exists(file_path):
        """Assert that a file exists."""
        assert os.path.exists(file_path), f"File does not exist: {file_path}"
    
    @staticmethod
    def assert_file_not_empty(file_path):
        """Assert that a file exists and is not empty."""
        assert os.path.exists(file_path), f"File does not exist: {file_path}"
        assert os.path.getsize(file_path) > 0, f"File is empty: {file_path}"
    
    @staticmethod
    def create_test_file(file_path, content=None):
        """Create a test file with optional content."""
        with open(file_path, "wb") as f:
            if content:
                f.write(content)
            else:
                # Create a small file with some content
                f.write(b"Test file content")
