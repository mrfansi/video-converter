import os
import uuid
import time
import ffmpeg
import numpy as np
from PIL import Image
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any

from app.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_temp_directory() -> str:
    """
    Create a temporary directory for processing files
    
    Returns:
        str: Path to the temporary directory
    """
    # Create a unique directory name using timestamp and UUID
    temp_dir = os.path.join(settings.TEMP_DIR, f"{int(time.time())}_{uuid.uuid4().hex[:8]}")
    os.makedirs(temp_dir, exist_ok=True)
    logger.info(f"Created temporary directory: {temp_dir}")
    return temp_dir

def extract_frames(
    video_path: str, 
    output_dir: str, 
    fps: int = settings.DEFAULT_FPS,
    width: int = settings.DEFAULT_WIDTH,
    height: int = settings.DEFAULT_HEIGHT
) -> List[str]:
    """
    Extract frames from a video file using ffmpeg
    
    Args:
        video_path (str): Path to the video file
        output_dir (str): Directory to save extracted frames
        fps (int): Frames per second to extract
        width (int): Width to resize frames to
        height (int): Height to resize frames to
        
    Returns:
        List[str]: List of paths to extracted frame images
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Define output pattern for frames
        output_pattern = os.path.join(output_dir, "frame_%04d.png")
        
        # Extract frames using ffmpeg
        (
            ffmpeg
            .input(video_path)
            .filter('fps', fps=fps)
            .filter('scale', width, height)
            .output(output_pattern)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        # Get list of extracted frames
        frame_files = sorted([
            os.path.join(output_dir, f) for f in os.listdir(output_dir)
            if f.startswith("frame_") and f.endswith(".png")
        ])
        
        logger.info(f"Extracted {len(frame_files)} frames from video")
        return frame_files
        
    except ffmpeg.Error as e:
        logger.error(f"Error extracting frames: {e.stderr.decode()}")
        raise RuntimeError(f"Failed to extract frames: {e.stderr.decode()}")
    except Exception as e:
        logger.error(f"Unexpected error extracting frames: {str(e)}")
        raise

def prepare_frame_for_tracing(image_path: str) -> str:
    """
    Prepare an image for tracing by enhancing contrast and reducing noise
    
    Args:
        image_path (str): Path to the image
        
    Returns:
        str: Path to the processed image
    """
    try:
        # Open image
        img = Image.open(image_path)
        
        # Convert to grayscale
        img = img.convert('L')
        
        # Enhance contrast
        pixels = np.array(img)
        pixels = np.interp(pixels, (pixels.min(), pixels.max()), (0, 255)).astype(np.uint8)
        img = Image.fromarray(pixels)
        
        # Save processed image (overwrite original)
        img.save(image_path)
        
        return image_path
        
    except Exception as e:
        logger.error(f"Error preparing frame for tracing: {str(e)}")
        raise

def cleanup_temp_files(directory: str) -> None:
    """
    Clean up temporary files and directories
    
    Args:
        directory (str): Directory to clean up
    """
    try:
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))
            os.rmdir(directory)
            logger.info(f"Cleaned up temporary directory: {directory}")
    except Exception as e:
        logger.warning(f"Error cleaning up temporary files: {str(e)}")
