"""Concrete strategies for video processing.

This module provides concrete implementations for video processing strategies
following the Strategy pattern for improved maintainability and extensibility.
"""

import os
import logging
from typing import Dict, Any, Optional, Callable

from app.infrastructure.video_processing.base_strategies import (
    BaseVideoProcessingStrategy,
)

logger = logging.getLogger(__name__)


class StandardVideoProcessingStrategy(BaseVideoProcessingStrategy):
    """Standard video processing strategy.

    This strategy provides a balanced approach to video processing,
    with good quality and reasonable processing time.
    """

    def process_video(
        self,
        file_path: str,
        output_dir: str,
        temp_dir: str,
        fps: int,
        width: Optional[int] = None,
        height: Optional[int] = None,
        original_filename: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Process a video file into a Lottie animation using the standard strategy.

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
        try:
            # Step 1: Extract frames from the video
            from app.infrastructure.frame_extractor import FrameExtractor
            from app.models.video_params import (
                FrameExtractionParamBuilder,
                FrameExtractionMethod,
            )

            frame_params = (
                FrameExtractionParamBuilder()
                .with_input_path(file_path)
                .with_output_dir(os.path.join(temp_dir, "frames"))
                .with_fps(fps)
                .with_dimensions(width, height)
                .with_method(FrameExtractionMethod.FFMPEG)
                .with_progress_callback(progress_callback)
                .build()
            )

            frame_extractor = FrameExtractor()
            frame_paths = frame_extractor.extract_frames(frame_params)

            if not frame_paths:
                raise ValueError("Failed to extract frames from the video")

            # Step 2: Process frames to SVG
            if self.frame_processor is None:
                from app.infrastructure.video_processing.component_strategies import (
                    StandardFrameProcessor,
                )

                self.frame_processor = StandardFrameProcessor()

            svg_paths = self.frame_processor.process_frames(
                frame_paths=frame_paths[
                    : min(len(frame_paths), 100)
                ],  # Limit to 100 frames
                output_dir=os.path.join(temp_dir, "svg"),
                progress_callback=progress_callback,
            )

            if not svg_paths:
                raise ValueError("Failed to process frames to SVG")

            # Step 3: Generate Lottie animation
            if self.lottie_generator is None:
                from app.infrastructure.video_processing.component_strategies import (
                    StandardLottieGenerator,
                )

                self.lottie_generator = StandardLottieGenerator()

            lottie_output_path = os.path.join(output_dir, "animation.json")
            lottie_path = self.lottie_generator.generate_lottie(
                svg_paths=svg_paths,
                output_path=lottie_output_path,
                fps=fps,
                width=width or 512,
                height=height or 512,
                max_frames=100,
                optimize=True,
                compress=True,
            )

            # Step 4: Generate thumbnail
            if self.thumbnail_generator is None:
                from app.infrastructure.video_processing.component_strategies import (
                    StandardThumbnailGenerator,
                )

                self.thumbnail_generator = StandardThumbnailGenerator()

            thumbnail_path = self.thumbnail_generator.generate_thumbnail(
                frame_path=frame_paths[0],
                output_dir=output_dir,
                source_dimensions=(width, height) if width and height else None,
                maintain_aspect_ratio=True,
            )

            # Step 5: Upload files if cloud uploader is available
            result = {
                "lottie_path": lottie_path,
                "thumbnail_path": thumbnail_path,
                "frame_count": len(svg_paths),
                "duration": len(svg_paths) / fps if fps > 0 else 0,
            }

            if self.cloud_uploader is not None:
                lottie_upload = self.cloud_uploader.upload_file(
                    file_path=lottie_path,
                    content_type="application/json",
                    custom_key=f"lottie/{os.path.basename(lottie_path)}",
                )

                thumbnail_upload = self.cloud_uploader.upload_file(
                    file_path=thumbnail_path,
                    content_type="image/png",
                    custom_key=f"thumbnails/{os.path.basename(thumbnail_path)}",
                )

                result["lottie_url"] = lottie_upload.get("url")
                result["thumbnail_url"] = thumbnail_upload.get("url")

            # Step 6: Clean up temporary files
            self.cleanup_temp_files(temp_dir)

            return result

        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            raise ValueError(f"Failed to process video: {str(e)}")
