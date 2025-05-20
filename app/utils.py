import os
import uuid
import time
import ffmpeg
import cv2
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

def extract_frames(video_path: str, output_dir: str, fps: int = 24, width: int = None, height: int = None) -> List[str]:
    """
    Extract frames from a video file at a specified FPS using a combination of OpenCV and ffmpeg
    
    Args:
        video_path (str): Path to the video file
        output_dir (str): Directory to save the extracted frames
        fps (int): Frames per second to extract
        width (int): Width to resize frames to
        height (int): Height to resize frames to
        
    Returns:
        List[str]: List of paths to extracted frame images
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # First try with ffmpeg (more reliable for initial frame extraction)
        try:
            # Define output pattern for frames
            output_pattern = os.path.join(output_dir, "frame_%04d.png")
            
            # Build ffmpeg command
            scale_option = ""
            if width is not None and height is not None:
                scale_option = f",scale={width}:{height}"
            
            # Run ffmpeg command directly
            import subprocess
            ffmpeg_cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vf", f"fps={fps}{scale_option}",
                "-pix_fmt", "rgb24",
                "-q:v", "1",  # High quality
                output_pattern,
                "-y"  # Overwrite existing files
            ]
            
            logger.info(f"Running ffmpeg command: {' '.join(ffmpeg_cmd)}")
            process = subprocess.run(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if process.returncode != 0:
                logger.warning(f"ffmpeg extraction failed: {process.stderr}")
                raise Exception("ffmpeg extraction failed")
                
            # Get the extracted frames
            frame_files = sorted([
                os.path.join(output_dir, f) for f in os.listdir(output_dir)
                if f.startswith("frame_") and f.endswith(".png")
            ])
            
            # Verify frames are not blank
            blank_count = 0
            for frame_file in frame_files[:5]:  # Check first few frames
                img = cv2.imread(frame_file)
                if img is None or np.mean(img) < 5 or np.std(img) < 3:
                    blank_count += 1
            
            if blank_count > 3 or len(frame_files) == 0:
                logger.warning(f"ffmpeg extraction produced {blank_count} blank frames out of 5 checked")
                raise Exception("ffmpeg extraction produced blank frames")
                
            logger.info(f"Successfully extracted {len(frame_files)} frames using ffmpeg")
            return frame_files
            
        except Exception as e:
            logger.warning(f"Falling back to OpenCV extraction: {str(e)}")
            # Clear the output directory for OpenCV extraction
            for f in os.listdir(output_dir):
                if f.startswith("frame_") and f.endswith(".png"):
                    os.remove(os.path.join(output_dir, f))
        
        # Fall back to OpenCV extraction
        logger.info(f"Opening video file with OpenCV: {video_path}")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video file: {video_path}")
        
        # Get video properties
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Use provided dimensions or original video dimensions
        target_width = width if width is not None else original_width
        target_height = height if height is not None else original_height
        
        logger.info(f"Video properties: {total_frames} frames, {video_fps} fps, {original_width}x{original_height}")
        logger.info(f"Target dimensions: {target_width}x{target_height}")
        
        # Calculate frame interval based on desired fps
        frame_interval = max(1, int(video_fps / fps))
        
        # Extract frames
        frame_files = []
        frame_count = 0
        
        # Use frame positions to extract evenly spaced frames
        num_frames = min(total_frames, int(total_frames / frame_interval))
        logger.info(f"Extracting {num_frames} frames at interval {frame_interval}")
        
        for i in range(num_frames):
            # Set position to exact frame we want
            frame_pos = i * frame_interval
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            
            # Read the frame
            ret, frame = cap.read()
            if not ret:
                logger.warning(f"Failed to read frame at position {frame_pos}")
                continue
            
            # Check if frame is blank
            mean_val = np.mean(frame)
            std_val = np.std(frame)
            if mean_val < 5 or std_val < 3:
                logger.warning(f"Frame at position {frame_pos} appears blank (mean={mean_val}, std={std_val})")
                continue
            
            # Resize frame if needed
            if target_width != original_width or target_height != original_height:
                frame = cv2.resize(frame, (target_width, target_height))
            
            # Save the frame
            frame_file = os.path.join(output_dir, f"frame_{i:04d}.png")
            cv2.imwrite(frame_file, frame)
            frame_files.append(frame_file)
            
            # Log progress
            if i % 10 == 0:
                logger.info(f"Extracted frame {i} at position {frame_pos}")
        
        # Release the video capture object
        cap.release()
        
        if len(frame_files) == 0:
            raise RuntimeError("Failed to extract any valid frames from video")
            
        logger.info(f"Successfully extracted {len(frame_files)} frames using OpenCV")
        return frame_files
        
    except Exception as e:
        logger.error(f"Error extracting frames: {str(e)}")
        raise

def prepare_frame_for_tracing(image_path: str) -> str:
    """
    Prepare an image for tracing by enhancing contrast and reducing noise
    while preserving color information
    
    Args:
        image_path (str): Path to the image
        
    Returns:
        str: Path to the processed image
    """
    try:
        # Open image (preserving color)
        img = Image.open(image_path)
        
        # Convert to RGB to ensure consistent color mode
        img = img.convert('RGB')
        
        # Enhance contrast for each channel while preserving color
        pixels = np.array(img)
        
        # Process each color channel separately
        for i in range(3):  # RGB channels
            channel = pixels[:,:,i]
            # Only enhance contrast if the channel has variation
            if channel.max() > channel.min():
                pixels[:,:,i] = np.interp(channel, (channel.min(), channel.max()), (0, 255)).astype(np.uint8)
        
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
