"""Domain interfaces for video processing strategies.

This module defines the interfaces for video processing strategies following
the Strategy pattern for improved maintainability and extensibility.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable


class IVideoProcessingStrategy(ABC):
    """Interface for video processing strategies.
    
    This interface defines the contract for video processing strategies
    that can process video files into Lottie animations.
    """
    
    @abstractmethod
    def process_video(self, file_path: str, output_dir: str, temp_dir: str,
                     fps: int, width: Optional[int] = None, height: Optional[int] = None,
                     original_filename: Optional[str] = None,
                     progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Process a video file into a Lottie animation.
        
        Args:
            file_path (str): Path to the video file
            output_dir (str): Directory to save the output files
            temp_dir (str): Temporary directory for processing
            fps (int): Frames per second for the animation
            width (Optional[int]): Width of the animation
            height (Optional[int]): Height of the animation
            original_filename (Optional[str]): Original filename of the uploaded video
            progress_callback (Optional[Callable]): Callback function for progress updates
            
        Returns:
            Dict[str, Any]: Processing result with URLs
            
        Raises:
            ValueError: If the input file is invalid or the processing fails
        """
        pass


class IFrameProcessor(ABC):
    """Interface for frame processing strategies.
    
    This interface defines the contract for strategies that process
    video frames into SVG files.
    """
    
    @abstractmethod
    def process_frames(self, frame_paths: List[str], output_dir: str,
                      progress_callback: Optional[Callable] = None) -> List[str]:
        """Process video frames into SVG files.
        
        Args:
            frame_paths (List[str]): Paths to the video frames
            output_dir (str): Directory to save the SVG files
            progress_callback (Optional[Callable]): Callback function for progress updates
            
        Returns:
            List[str]: Paths to the generated SVG files
            
        Raises:
            ValueError: If the input files are invalid or the processing fails
        """
        pass


class ILottieGenerator(ABC):
    """Interface for Lottie generation strategies.
    
    This interface defines the contract for strategies that generate
    Lottie animations from SVG files.
    """
    
    @abstractmethod
    def generate_lottie(self, svg_paths: List[str], output_path: str,
                       fps: int, width: int, height: int,
                       max_frames: int = 100, optimize: bool = True,
                       compress: bool = True) -> str:
        """Generate a Lottie animation from SVG files.
        
        Args:
            svg_paths (List[str]): Paths to the SVG files
            output_path (str): Path to save the Lottie animation
            fps (int): Frames per second for the animation
            width (int): Width of the animation
            height (int): Height of the animation
            max_frames (int): Maximum number of frames to include
            optimize (bool): Whether to optimize the animation
            compress (bool): Whether to compress the animation
            
        Returns:
            str: Path to the generated Lottie animation
            
        Raises:
            ValueError: If the input files are invalid or the generation fails
        """
        pass


class IThumbnailGenerator(ABC):
    """Interface for thumbnail generation strategies.
    
    This interface defines the contract for strategies that generate
    thumbnails from video frames.
    """
    
    @abstractmethod
    def generate_thumbnail(self, frame_path: str, output_dir: str,
                          source_dimensions: tuple = None,
                          maintain_aspect_ratio: bool = True) -> str:
        """Generate a thumbnail from a video frame.
        
        Args:
            frame_path (str): Path to the video frame
            output_dir (str): Directory to save the thumbnail
            source_dimensions (tuple): Source dimensions (width, height)
            maintain_aspect_ratio (bool): Whether to maintain aspect ratio
            
        Returns:
            str: Path to the generated thumbnail
            
        Raises:
            ValueError: If the input file is invalid or the generation fails
        """
        pass


class ICloudUploader(ABC):
    """Interface for cloud upload strategies.
    
    This interface defines the contract for strategies that upload
    files to cloud storage.
    """
    
    @abstractmethod
    def upload_file(self, file_path: str, content_type: str = None,
                   custom_key: str = None) -> Dict[str, Any]:
        """Upload a file to cloud storage.
        
        Args:
            file_path (str): Path to the file to upload
            content_type (str): Content type of the file
            custom_key (str): Custom key for the file
            
        Returns:
            Dict[str, Any]: Upload result with URL
            
        Raises:
            ValueError: If the upload fails
        """
        pass
