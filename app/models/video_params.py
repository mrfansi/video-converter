"""Parameter objects for video conversion functionality.

This module provides parameter objects for video conversion operations,
reducing function parameter complexity and improving code readability.
"""

from enum import Enum
import os
from typing import Optional, List, Union, Callable
from pydantic import Field, validator

from app.models.base_params import BaseParams, ParamBuilder


class VideoQuality(str, Enum):
    """Video quality presets."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class VideoResolution(str, Enum):
    """Standard video resolutions."""

    SD_480P = "480p"  # 854x480
    HD_720P = "720p"  # 1280x720
    HD_1080P = "1080p"  # 1920x1080
    UHD_4K = "4k"  # 3840x2160


class VideoFormat(str, Enum):
    """Supported video formats."""

    MP4 = "mp4"
    WEBM = "webm"
    GIF = "gif"
    MOV = "mov"
    AVI = "avi"


class VideoConversionParams(BaseParams):
    """Parameters for video conversion operations.

    This parameter object encapsulates all options for video conversion,
    replacing the need for numerous function parameters.
    """

    # Required parameters
    input_path: str = Field(..., description="Path to the input video file")
    output_dir: str = Field(..., description="Directory to save the output video")
    output_format: VideoFormat = Field(..., description="Output video format")

    # Optional parameters with defaults
    quality: VideoQuality = Field(
        default=VideoQuality.MEDIUM, description="Video quality preset"
    )
    resolution: Optional[VideoResolution] = Field(
        default=None, description="Output video resolution"
    )
    framerate: Optional[int] = Field(default=None, description="Output video framerate")
    start_time: Optional[float] = Field(
        default=None, description="Start time in seconds"
    )
    end_time: Optional[float] = Field(default=None, description="End time in seconds")
    audio_codec: Optional[str] = Field(default=None, description="Audio codec to use")
    video_codec: Optional[str] = Field(default=None, description="Video codec to use")
    bitrate: Optional[str] = Field(default=None, description="Video bitrate")
    audio_bitrate: Optional[str] = Field(default=None, description="Audio bitrate")
    extra_ffmpeg_params: Optional[List[str]] = Field(
        default=None, description="Additional ffmpeg parameters"
    )

    # Callback for progress tracking
    progress_callback: Optional[Callable[[int], None]] = Field(
        default=None, description="Callback function for progress updates"
    )

    @validator("input_path")
    def validate_input_path(cls, v):
        """Validate that input path is not empty."""
        if not v or not v.strip():
            raise ValueError("Input path cannot be empty")
        return v

    @validator("output_dir")
    def validate_output_dir(cls, v):
        """Validate that output directory is not empty."""
        if not v or not v.strip():
            raise ValueError("Output directory cannot be empty")
        return v

    @validator("framerate")
    def validate_framerate(cls, v):
        """Validate that framerate is positive."""
        if v is not None and v <= 0:
            raise ValueError("Framerate must be positive")
        return v

    @validator("start_time", "end_time")
    def validate_time(cls, v):
        """Validate that time values are non-negative."""
        if v is not None and v < 0:
            raise ValueError("Time values must be non-negative")
        return v

    def get_quality_crf(self) -> int:
        """Get the CRF (Constant Rate Factor) value for the selected quality.

        Returns:
            int: CRF value (lower is higher quality)
        """
        crf_map = {VideoQuality.LOW: 28, VideoQuality.MEDIUM: 23, VideoQuality.HIGH: 18}
        return crf_map[self.quality]

    def get_resolution_dimensions(self) -> Optional[str]:
        """Get the dimensions for the selected resolution.

        Returns:
            Optional[str]: Dimensions in the format "widthxheight" or None if no resolution specified
        """
        if not self.resolution:
            return None

        dimensions_map = {
            VideoResolution.SD_480P: "854x480",
            VideoResolution.HD_720P: "1280x720",
            VideoResolution.HD_1080P: "1920x1080",
            VideoResolution.UHD_4K: "3840x2160",
        }
        return dimensions_map[self.resolution]


class VideoConversionParamBuilder(ParamBuilder[VideoConversionParams]):
    """Builder for VideoConversionParams.

    Provides a fluent interface for building video conversion parameters.
    """

    def __init__(self):
        """Initialize the builder with the VideoConversionParams class."""
        super().__init__(VideoConversionParams)

    def with_input_path(self, input_path: str) -> "VideoConversionParamBuilder":
        """Set the input video path."""
        return self.with_param("input_path", input_path)

    def with_output_dir(self, output_dir: str) -> "VideoConversionParamBuilder":
        """Set the output directory."""
        return self.with_param("output_dir", output_dir)

    def with_format(
        self, format: Union[VideoFormat, str]
    ) -> "VideoConversionParamBuilder":
        """Set the output format."""
        if isinstance(format, str):
            format = VideoFormat(format)
        return self.with_param("output_format", format)

    def with_quality(
        self, quality: Union[VideoQuality, str]
    ) -> "VideoConversionParamBuilder":
        """Set the video quality."""
        if isinstance(quality, str):
            quality = VideoQuality(quality)
        return self.with_param("quality", quality)

    def with_resolution(
        self, resolution: Union[VideoResolution, str]
    ) -> "VideoConversionParamBuilder":
        """Set the video resolution."""
        if isinstance(resolution, str):
            resolution = VideoResolution(resolution)
        return self.with_param("resolution", resolution)

    def with_framerate(self, framerate: int) -> "VideoConversionParamBuilder":
        """Set the video framerate."""
        return self.with_param("framerate", framerate)

    def with_time_range(
        self, start_time: float, end_time: float
    ) -> "VideoConversionParamBuilder":
        """Set the video time range."""
        self.with_param("start_time", start_time)
        return self.with_param("end_time", end_time)

    def with_codecs(
        self, video_codec: str, audio_codec: Optional[str] = None
    ) -> "VideoConversionParamBuilder":
        """Set the video and audio codecs."""
        self.with_param("video_codec", video_codec)
        if audio_codec:
            self.with_param("audio_codec", audio_codec)
        return self

    def with_bitrates(
        self, video_bitrate: str, audio_bitrate: Optional[str] = None
    ) -> "VideoConversionParamBuilder":
        """Set the video and audio bitrates."""
        self.with_param("bitrate", video_bitrate)
        if audio_bitrate:
            self.with_param("audio_bitrate", audio_bitrate)
        return self

    def with_extra_ffmpeg_params(
        self, params: List[str]
    ) -> "VideoConversionParamBuilder":
        """Set additional ffmpeg parameters."""
        return self.with_param("extra_ffmpeg_params", params)

    def with_progress_callback(
        self, callback: Callable[[int], None]
    ) -> "VideoConversionParamBuilder":
        """Set the progress callback function."""
        return self.with_param("progress_callback", callback)


class FrameExtractionMethod(str, Enum):
    """Frame extraction methods."""

    FFMPEG = "ffmpeg"  # Use ffmpeg for extraction (more reliable for most videos)
    OPENCV = "opencv"  # Use OpenCV for extraction (more control over frame processing)
    HYBRID = "hybrid"  # Try ffmpeg first, fall back to OpenCV if it fails


class FrameExtractionParams(BaseParams):
    """Parameters for frame extraction operations.

    This parameter object encapsulates all options for frame extraction,
    replacing the need for numerous function parameters.
    """

    # Required parameters
    input_path: str = Field(..., description="Path to the input video file")
    output_dir: str = Field(..., description="Directory to save the extracted frames")

    # Optional parameters with defaults
    fps: int = Field(default=24, description="Frames per second to extract")
    width: Optional[int] = Field(default=None, description="Width to resize frames to")
    height: Optional[int] = Field(
        default=None, description="Height to resize frames to"
    )
    extraction_method: FrameExtractionMethod = Field(
        default=FrameExtractionMethod.HYBRID,
        description="Method to use for frame extraction",
    )
    quality: int = Field(default=90, description="Quality of extracted frames (1-100)")
    start_time: Optional[float] = Field(
        default=None, description="Start time in seconds"
    )
    end_time: Optional[float] = Field(default=None, description="End time in seconds")
    frame_prefix: str = Field(
        default="frame_", description="Prefix for frame filenames"
    )
    frame_format: str = Field(default="png", description="Format for extracted frames")

    # Advanced options
    blank_threshold_mean: float = Field(
        default=5.0, description="Mean pixel value threshold for blank frame detection"
    )
    blank_threshold_std: float = Field(
        default=3.0,
        description="Standard deviation threshold for blank frame detection",
    )
    extra_ffmpeg_params: Optional[List[str]] = Field(
        default=None, description="Additional ffmpeg parameters"
    )

    # Callback for progress tracking
    progress_callback: Optional[Callable[[int, int], None]] = Field(
        default=None,
        description="Callback function for progress updates (current_frame, total_frames)",
    )

    @validator("input_path")
    def validate_input_path(cls, v):
        """Validate that input path is not empty."""
        if not v or not v.strip():
            raise ValueError("Input path cannot be empty")
        return v

    @validator("output_dir")
    def validate_output_dir(cls, v):
        """Validate that output directory is not empty."""
        if not v or not v.strip():
            raise ValueError("Output directory cannot be empty")
        return v

    @validator("fps")
    def validate_fps(cls, v):
        """Validate that fps is positive."""
        if v <= 0:
            raise ValueError("FPS must be positive")
        return v

    @validator("quality")
    def validate_quality(cls, v):
        """Validate that quality is between 1 and 100."""
        if v < 1 or v > 100:
            raise ValueError("Quality must be between 1 and 100")
        return v

    @validator("start_time", "end_time")
    def validate_time(cls, v):
        """Validate that time values are non-negative."""
        if v is not None and v < 0:
            raise ValueError("Time values must be non-negative")
        return v

    def get_frame_filename(self, frame_number: int) -> str:
        """Get the filename for a frame.

        Args:
            frame_number (int): Frame number

        Returns:
            str: Filename for the frame
        """
        return f"{self.frame_prefix}{frame_number:04d}.{self.frame_format}"

    def get_output_path(self, frame_number: int) -> str:
        """Get the full output path for a frame.

        Args:
            frame_number (int): Frame number

        Returns:
            str: Full output path for the frame
        """
        return os.path.join(self.output_dir, self.get_frame_filename(frame_number))


class FrameExtractionParamBuilder(ParamBuilder[FrameExtractionParams]):
    """Builder for FrameExtractionParams.

    Provides a fluent interface for building frame extraction parameters.
    """

    def __init__(self):
        """Initialize the builder with the FrameExtractionParams class."""
        super().__init__(FrameExtractionParams)

    def with_input_path(self, input_path: str) -> "FrameExtractionParamBuilder":
        """Set the input video path."""
        return self.with_param("input_path", input_path)

    def with_output_dir(self, output_dir: str) -> "FrameExtractionParamBuilder":
        """Set the output directory."""
        return self.with_param("output_dir", output_dir)

    def with_fps(self, fps: int) -> "FrameExtractionParamBuilder":
        """Set the frames per second to extract."""
        return self.with_param("fps", fps)

    def with_dimensions(self, width: int, height: int) -> "FrameExtractionParamBuilder":
        """Set the dimensions to resize frames to."""
        self.with_param("width", width)
        return self.with_param("height", height)

    def with_extraction_method(
        self, method: Union[FrameExtractionMethod, str]
    ) -> "FrameExtractionParamBuilder":
        """Set the extraction method."""
        if isinstance(method, str):
            method = FrameExtractionMethod(method)
        return self.with_param("extraction_method", method)

    def with_quality(self, quality: int) -> "FrameExtractionParamBuilder":
        """Set the quality of extracted frames."""
        return self.with_param("quality", quality)

    def with_time_range(
        self, start_time: float, end_time: float
    ) -> "FrameExtractionParamBuilder":
        """Set the video time range."""
        self.with_param("start_time", start_time)
        return self.with_param("end_time", end_time)

    def with_frame_naming(
        self, prefix: str, format: str
    ) -> "FrameExtractionParamBuilder":
        """Set the frame naming options."""
        self.with_param("frame_prefix", prefix)
        return self.with_param("frame_format", format)

    def with_blank_detection(
        self, mean_threshold: float, std_threshold: float
    ) -> "FrameExtractionParamBuilder":
        """Set the blank frame detection thresholds."""
        self.with_param("blank_threshold_mean", mean_threshold)
        return self.with_param("blank_threshold_std", std_threshold)

    def with_extra_ffmpeg_params(
        self, params: List[str]
    ) -> "FrameExtractionParamBuilder":
        """Set additional ffmpeg parameters."""
        return self.with_param("extra_ffmpeg_params", params)

    def with_progress_callback(
        self, callback: Callable[[int, int], None]
    ) -> "FrameExtractionParamBuilder":
        """Set the progress callback function."""
        return self.with_param("progress_callback", callback)
