import os
import json
import time
import cv2
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from PIL import Image, ImageDraw

from app.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_thumbnail_from_frame(frame_path: str, output_dir: str, size: Tuple[int, int] = (400, 400)) -> str:
    """
    Generate a thumbnail image from a video frame
    
    Args:
        frame_path (str): Path to the frame image
        output_dir (str): Directory to save the thumbnail
        size (Tuple[int, int]): Thumbnail size (width, height)
        
    Returns:
        str: Path to the generated thumbnail
    """
    try:
        # Create output filename
        thumbnail_path = os.path.join(output_dir, "thumbnail.png")
        
        # Open the image with PIL
        img = Image.open(frame_path)
        
        # Resize the image to thumbnail size
        img.thumbnail(size, Image.LANCZOS)
        
        # Save the thumbnail
        img.save(thumbnail_path, "PNG")
        
        logger.info(f"Generated thumbnail at {thumbnail_path}")
        return thumbnail_path
        
    except Exception as e:
        logger.error(f"Error generating thumbnail: {str(e)}")
        raise

def generate_thumbnail_from_lottie(lottie_json: Dict[str, Any], output_dir: str, size: Tuple[int, int] = (400, 400)) -> str:
    """
    Generate a thumbnail image from a Lottie JSON animation
    
    Args:
        lottie_json (Dict[str, Any]): Lottie animation JSON
        output_dir (str): Directory to save the thumbnail
        size (Tuple[int, int]): Thumbnail size (width, height)
        
    Returns:
        str: Path to the generated thumbnail
    """
    try:
        # Create output filename
        thumbnail_path = os.path.join(output_dir, "thumbnail.png")
        
        # Get dimensions from Lottie JSON
        width = lottie_json.get("w", 800)
        height = lottie_json.get("h", 600)
        
        # Create a blank image with white background
        img = Image.new("RGBA", (width, height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Draw a representation of the first frame of the animation
        # This is a simplified representation since we can't render the actual Lottie animation
        # without a JavaScript runtime
        
        # Draw a border
        draw.rectangle([(0, 0), (width-1, height-1)], outline=(200, 200, 200), width=2)
        
        # Draw a Lottie icon/text
        font_size = min(width, height) // 10
        text_position = (width // 2 - font_size * 2, height // 2 - font_size // 2)
        draw.text(text_position, "Lottie", fill=(0, 0, 0))
        
        # Add some info text
        info_text = f"{width}x{height}, {lottie_json.get('fr', 30)}fps"
        info_position = (width // 2 - font_size * 2, height // 2 + font_size)
        draw.text(info_position, info_text, fill=(100, 100, 100))
        
        # Resize the image to thumbnail size
        img.thumbnail(size, Image.LANCZOS)
        
        # Save the thumbnail
        img.save(thumbnail_path, "PNG")
        
        logger.info(f"Generated Lottie thumbnail at {thumbnail_path}")
        return thumbnail_path
        
    except Exception as e:
        logger.error(f"Error generating Lottie thumbnail: {str(e)}")
        raise

def upload_thumbnail(thumbnail_path: str, uploader: Any, object_key: str) -> Dict[str, Any]:
    """
    Upload a thumbnail to Cloudflare R2
    
    Args:
        thumbnail_path (str): Path to the thumbnail image
        uploader (Any): Uploader instance
        object_key (str): Object key for the related Lottie JSON
        
    Returns:
        Dict[str, Any]: Upload result with URL
    """
    try:
        # Generate thumbnail object key based on the Lottie JSON object key
        thumbnail_key = object_key.replace(".json", ".png")
        
        # Upload the thumbnail
        result = uploader.upload_file(thumbnail_path, content_type="image/png", custom_key=thumbnail_key)
        
        logger.info(f"Uploaded thumbnail to {result.get('url')}")
        return result
        
    except Exception as e:
        logger.error(f"Error uploading thumbnail: {str(e)}")
        raise
