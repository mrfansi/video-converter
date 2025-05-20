import os
import sys
import unittest
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.utils import create_temp_directory, cleanup_temp_files
from app.uploader import CloudflareR2Uploader

class TestComponents(unittest.TestCase):
    """Test basic functionality of components"""
    
    def test_temp_directory_creation(self):
        """Test that temporary directories can be created and cleaned up"""
        temp_dir = create_temp_directory()
        self.assertTrue(os.path.exists(temp_dir))
        
        # Create a test file in the directory
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        
        self.assertTrue(os.path.exists(test_file))
        
        # Clean up
        cleanup_temp_files(temp_dir)
        self.assertFalse(os.path.exists(temp_dir))
    
    def test_r2_uploader_initialization(self):
        """Test that the R2 uploader can be initialized"""
        uploader = CloudflareR2Uploader()
        self.assertIsNotNone(uploader.client)
        
        # Note: This doesn't test actual uploads since that requires valid credentials

if __name__ == "__main__":
    # Create tests directory if it doesn't exist
    os.makedirs("tests", exist_ok=True)
    
    unittest.main()
