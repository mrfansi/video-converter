"""Parameter objects for video format task processing.

This module provides parameter objects for video format task processing
to improve maintainability and extensibility.
"""

from typing import Optional, Callable, Union
from pydantic import BaseModel, Field, validator

from app.infrastructure.video_format_task.task_processor import VideoFormatTaskStrategy


class VideoFormatTaskParams(BaseModel):
    """Parameters for video format task processing."""

    temp_dir: str = Field(..., description="Temporary directory for processing")
    file_path: str = Field(..., description="Path to the uploaded video file")
    output_format: str = Field(
        ..., description="Desired output format (mp4, webm, etc.)"
    )
    quality: str = Field(
        "medium", description="Quality preset (low, medium, high, veryhigh)"
    )
    width: Optional[int] = Field(None, description="Output width")
    height: Optional[int] = Field(None, description="Output height")
    bitrate: Optional[str] = Field(
        None, description='Video bitrate (e.g., "1M" for 1 Mbps)'
    )
    preset: str = Field("medium", description="Encoding preset (ultrafast to veryslow)")
    crf: Optional[int] = Field(
        None, description="Constant Rate Factor (0-51, lower means better quality)"
    )
    audio_codec: Optional[str] = Field(
        None, description="Audio codec (aac, mp3, opus, etc.)"
    )
    audio_bitrate: Optional[str] = Field(
        None, description='Audio bitrate (e.g., "128k")'
    )
    original_filename: Optional[str] = Field(
        None, description="Original filename of the uploaded video"
    )
    task_id: Optional[str] = Field(None, description="Task ID for progress tracking")
    strategy: VideoFormatTaskStrategy = Field(
        VideoFormatTaskStrategy.STANDARD, description="Strategy to use for processing"
    )
    progress_callback: Optional[Callable] = Field(
        None, description="Callback function for progress updates"
    )

    @validator("quality")
    def validate_quality(cls, v):
        """Validate the quality parameter."""
        valid_qualities = ["low", "medium", "high", "veryhigh"]
        if v not in valid_qualities:
            raise ValueError(f"Quality must be one of {valid_qualities}")
        return v

    @validator("preset")
    def validate_preset(cls, v):
        """Validate the preset parameter."""
        valid_presets = [
            "ultrafast",
            "superfast",
            "veryfast",
            "faster",
            "fast",
            "medium",
            "slow",
            "slower",
            "veryslow",
        ]
        if v not in valid_presets:
            raise ValueError(f"Preset must be one of {valid_presets}")
        return v

    @validator("crf")
    def validate_crf(cls, v):
        """Validate the CRF parameter."""
        if v is not None and (v < 0 or v > 51):
            raise ValueError("CRF must be between 0 and 51")
        return v

    @validator("width", "height")
    def validate_dimensions(cls, v):
        """Validate the width and height parameters."""
        if v is not None and v <= 0:
            raise ValueError("Dimensions must be positive")
        return v

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class VideoFormatTaskParamBuilder:
    """Builder for VideoFormatTaskParams."""

    def __init__(self):
        """Initialize the builder."""
        self.params = {}

    def with_temp_dir(self, temp_dir: str) -> "VideoFormatTaskParamBuilder":
        """Set the temporary directory."""
        self.params["temp_dir"] = temp_dir
        return self

    def with_file_path(self, file_path: str) -> "VideoFormatTaskParamBuilder":
        """Set the file path."""
        self.params["file_path"] = file_path
        return self

    def with_output_format(self, output_format: str) -> "VideoFormatTaskParamBuilder":
        """Set the output format."""
        self.params["output_format"] = output_format
        return self

    def with_quality(self, quality: str) -> "VideoFormatTaskParamBuilder":
        """Set the quality."""
        self.params["quality"] = quality
        return self

    def with_dimensions(
        self, width: Optional[int] = None, height: Optional[int] = None
    ) -> "VideoFormatTaskParamBuilder":
        """Set the dimensions."""
        if width is not None:
            self.params["width"] = width
        if height is not None:
            self.params["height"] = height
        return self

    def with_bitrate(self, bitrate: str) -> "VideoFormatTaskParamBuilder":
        """Set the bitrate."""
        self.params["bitrate"] = bitrate
        return self

    def with_preset(self, preset: str) -> "VideoFormatTaskParamBuilder":
        """Set the preset."""
        self.params["preset"] = preset
        return self

    def with_crf(self, crf: int) -> "VideoFormatTaskParamBuilder":
        """Set the CRF."""
        self.params["crf"] = crf
        return self

    def with_audio_codec(self, audio_codec: str) -> "VideoFormatTaskParamBuilder":
        """Set the audio codec."""
        self.params["audio_codec"] = audio_codec
        return self

    def with_audio_bitrate(self, audio_bitrate: str) -> "VideoFormatTaskParamBuilder":
        """Set the audio bitrate."""
        self.params["audio_bitrate"] = audio_bitrate
        return self

    def with_original_filename(
        self, original_filename: str
    ) -> "VideoFormatTaskParamBuilder":
        """Set the original filename."""
        self.params["original_filename"] = original_filename
        return self

    def with_task_id(self, task_id: str) -> "VideoFormatTaskParamBuilder":
        """Set the task ID."""
        self.params["task_id"] = task_id
        return self

    def with_strategy(
        self, strategy: Union[VideoFormatTaskStrategy, str]
    ) -> "VideoFormatTaskParamBuilder":
        """Set the strategy."""
        if isinstance(strategy, str):
            strategy = VideoFormatTaskStrategy(strategy)
        self.params["strategy"] = strategy
        return self

    def with_progress_callback(
        self, progress_callback: Callable
    ) -> "VideoFormatTaskParamBuilder":
        """Set the progress callback."""
        self.params["progress_callback"] = progress_callback
        return self

    def build(self) -> VideoFormatTaskParams:
        """Build the parameters."""
        return VideoFormatTaskParams(**self.params)
