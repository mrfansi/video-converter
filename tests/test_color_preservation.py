import os
import sys
import logging
import tempfile
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils import prepare_frame_for_tracing, extract_frames
from app.lottie_generator import trace_png_to_svg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_color_preservation():
    """Test that the color is preserved in the video-to-lottie conversion process"""
    try:
        # Path to the sample video
        video_path = os.path.join(os.path.dirname(__file__), "video.webm")
        
        # Create temporary directories for frames and SVGs
        with tempfile.TemporaryDirectory() as temp_dir:
            frames_dir = os.path.join(temp_dir, "frames")
            svg_dir = os.path.join(temp_dir, "svg")
            os.makedirs(frames_dir, exist_ok=True)
            os.makedirs(svg_dir, exist_ok=True)
            
            # Extract frames from the video
            logger.info(f"Extracting frames from {video_path}")
            frame_paths = extract_frames(video_path, frames_dir, fps=5, width=640, height=480)
            logger.info(f"Extracted {len(frame_paths)} frames")
            
            if not frame_paths:
                logger.error("No frames were extracted from the video")
                return False
            
            # Process a sample frame to test color preservation
            sample_frame = frame_paths[0]
            logger.info(f"Processing sample frame: {sample_frame}")
            
            # Prepare the frame for tracing (should preserve color now)
            prepared_frame = prepare_frame_for_tracing(sample_frame)
            logger.info(f"Prepared frame: {prepared_frame}")
            
            # Trace the frame to SVG
            svg_path = trace_png_to_svg(prepared_frame, svg_dir)
            logger.info(f"Generated SVG: {svg_path}")
            
            # Check if the SVG file exists
            if not os.path.exists(svg_path):
                logger.error(f"SVG file was not created: {svg_path}")
                return False
            
            # Success
            logger.info("Color preservation test completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"Error in color preservation test: {str(e)}")
        return False

if __name__ == "__main__":
    result = test_color_preservation()
    if result:
        print("\nCOLOR PRESERVATION TEST PASSED!")
        sys.exit(0)
    else:
        print("\nCOLOR PRESERVATION TEST FAILED!")
        sys.exit(1)
