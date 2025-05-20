import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # API settings
    API_TITLE: str = "Video Converter API"
    API_DESCRIPTION: str = """
    This API converts video files to Lottie animations and between different video formats with optimization.
    
    ## Features
    
    * Upload video files (.mp4, .mov, .avi, .webm, .mkv, .flv, .wmv, .m4v)
    * Convert videos to Lottie JSON animations
    * Convert videos between different formats with optimization options
    * Background processing with real-time progress tracking
    * Generate thumbnails from videos
    * Store results in Cloudflare R2
    
    ## Workflow
    
    1. Upload a video using the `/upload` endpoint for Lottie conversion or `/convert` for format conversion
    2. Receive a task ID and status endpoint
    3. Poll the status endpoint to track progress
    4. When complete, receive URLs to the processed files
    """
    API_VERSION: str = "1.0.0"
    
    # Processing settings
    DEFAULT_FPS: int = 30
    DEFAULT_WIDTH: int = 800
    DEFAULT_HEIGHT: int = 600
    TEMP_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media")
    
    # Cloudflare R2 settings
    R2_ENDPOINT_URL: str = os.getenv("R2_ENDPOINT_URL", "")
    R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID", "")
    R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
    R2_BUCKET_NAME: str = os.getenv("R2_BUCKET_NAME", "lottie-animations")
    R2_PATH_PREFIX: str = os.getenv("R2_PATH_PREFIX", "lottie")
    R2_URL: str = os.getenv("R2_URL", "")  # Custom domain for R2 public access
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()
