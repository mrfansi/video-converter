"""Domain interfaces for frame extraction strategies.

This module defines the interfaces for frame extraction strategies following
the Strategy pattern for improved maintainability and extensibility.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class IFrameExtractionStrategy(ABC):
    """Interface for frame extraction strategies.
    
    This interface defines the contract for frame extraction strategies
    that can extract frames from video files.
    """
    
    @abstractmethod
    def extract_frames(self, video_path: str, output_dir: str, fps: int = 24, 
                      width: Optional[int] = None, height: Optional[int] = None) -> List[str]:
        """Extract frames from a video file.
        
        Args:
            video_path (str): Path to the video file
            output_dir (str): Directory to save the extracted frames
            fps (int): Frames per second to extract
            width (Optional[int]): Width to resize frames to
            height (Optional[int]): Height to resize frames to
            
        Returns:
            List[str]: List of paths to extracted frame images
            
        Raises:
            ValueError: If the input file is invalid or the extraction fails
        """
        pass


class IFrameQualityValidator(ABC):
    """Interface for frame quality validation strategies.
    
    This interface defines the contract for strategies that validate
    the quality of extracted frames.
    """
    
    @abstractmethod
    def validate_frame(self, frame) -> bool:
        """Validate the quality of a frame.
        
        Args:
            frame: The frame to validate (OpenCV image)
            
        Returns:
            bool: True if the frame is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def validate_frame_file(self, frame_path: str) -> bool:
        """Validate the quality of a frame file.
        
        Args:
            frame_path (str): Path to the frame file
            
        Returns:
            bool: True if the frame is valid, False otherwise
        """
        pass


class IFrameResizer(ABC):
    """Interface for frame resizing strategies.
    
    This interface defines the contract for strategies that resize
    extracted frames.
    """
    
    @abstractmethod
    def resize_frame(self, frame, target_width: int, target_height: int):
        """Resize a frame to the target dimensions.
        
        Args:
            frame: The frame to resize (OpenCV image)
            target_width (int): Target width
            target_height (int): Target height
            
        Returns:
            The resized frame
        """
        pass


class IFrameWriter(ABC):
    """Interface for frame writing strategies.
    
    This interface defines the contract for strategies that write
    frames to disk.
    """
    
    @abstractmethod
    def write_frame(self, frame, output_path: str) -> str:
        """Write a frame to disk.
        
        Args:
            frame: The frame to write (OpenCV image)
            output_path (str): Path to write the frame to
            
        Returns:
            str: Path to the written frame
        """
        pass
