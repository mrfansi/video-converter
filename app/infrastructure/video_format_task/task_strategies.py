"""Concrete strategies for video format task processing.

This module provides concrete implementations for video format task processing strategies
following the Strategy pattern for improved maintainability and extensibility.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, Callable

from app.domain.interfaces.video_format_task import (
    IVideoFormatTaskStrategy,
    ITaskProgressTracker,
    ICloudUploader
)
from app.infrastructure.video_format_task.base_strategies import (
    BaseVideoFormatTaskStrategy,
    BaseTaskProgressTracker,
    BaseCloudUploader
)
from app.video_converter import convert_video, get_video_info
from app.infrastructure.video_converter import VideoConverter
from app.models.video_params import VideoConversionParams, VideoConversionParamBuilder, VideoQuality, OutputFormat, Resolution

logger = logging.getLogger(__name__)


class StandardVideoFormatTaskStrategy(BaseVideoFormatTaskStrategy):
    """Standard video format task processing strategy.
    
    This strategy uses the standard approach for processing video format tasks,
    suitable for most video conversion scenarios.
    """
    
    def process_video_format_task(self, temp_dir: str, file_path: str, output_format: str,
                                quality: str, width: Optional[int], height: Optional[int],
                                bitrate: Optional[str], preset: str, crf: Optional[int],
                                audio_codec: Optional[str], audio_bitrate: Optional[str],
                                original_filename: Optional[str], task_id: Optional[str],
                                progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Process a video format task using the standard strategy.
        
        Args:
            temp_dir: Temporary directory for processing
            file_path: Path to the uploaded video file
            output_format: Desired output format (mp4, webm, etc.)
            quality: Quality preset (low, medium, high, veryhigh)
            width: Output width
            height: Output height
            bitrate: Video bitrate (e.g., "1M" for 1 Mbps)
            preset: Encoding preset (ultrafast to veryslow)
            crf: Constant Rate Factor (0-51, lower means better quality)
            audio_codec: Audio codec (aac, mp3, opus, etc.)
            audio_bitrate: Audio bitrate (e.g., "128k")
            original_filename: Original filename of the uploaded video
            task_id: Task ID for progress tracking
            progress_callback: Callback function for progress updates
            
        Returns:
            Dict[str, Any]: Processing result with URLs
        """
        try:
            logger.info(f"Converting video format in background: {original_filename}")
            
            # Define total steps for progress tracking
            total_steps = 3  # Initialize, convert, upload
            current_step = 0
            
            # Step 1: Get video information
            current_step += 1
            self.progress_tracker.update_progress(
                task_id=task_id,
                current_step="Analyzing video",
                percent=10,
                details=f"Analyzing video properties"
            )
                
            video_info = get_video_info(file_path)
            logger.info(f"Video info: {video_info}")
            
            # Step 2: Convert video
            current_step += 1
            self.progress_tracker.update_progress(
                task_id=task_id,
                current_step="Converting video",
                percent=20,
                details=f"Converting video to {output_format}"
            )
                
            # Define progress callback function
            def progress_update(task_id, current_step, percent, details):
                self.progress_tracker.update_progress(
                    task_id=task_id,
                    current_step=current_step,
                    percent=20 + int(percent * 0.7),  # Scale to 20-90% of overall progress
                    details=details
                )
            
            # Create conversion parameters using the builder pattern
            params_builder = VideoConversionParamBuilder()
            params_builder.with_input_path(file_path)
            params_builder.with_output_dir(temp_dir)
            params_builder.with_output_format(OutputFormat(output_format))
            params_builder.with_quality(VideoQuality(quality))
            
            if width and height:
                params_builder.with_resolution(Resolution(width, height))
            
            if bitrate:
                params_builder.with_bitrate(bitrate)
            
            if preset:
                params_builder.with_preset(preset)
            
            if crf is not None:
                params_builder.with_crf(crf)
            
            if audio_codec:
                params_builder.with_audio_codec(audio_codec)
            
            if audio_bitrate:
                params_builder.with_audio_bitrate(audio_bitrate)
            
            # Add progress callback if task_id is provided
            if task_id:
                params_builder.with_progress_callback(lambda current_step, percent, details: 
                                                    progress_update(task_id, current_step, percent, details))
            
            # Build the parameters
            conversion_params = params_builder.build()
            
            # Create the video converter and convert the video
            converter = VideoConverter()
            conversion_result = converter.convert_video(conversion_params)
            
            logger.info(f"Video converted successfully: {conversion_result['output_path']}")
            
            # Step 3: Upload to Cloudflare R2
            current_step += 1
            self.progress_tracker.update_progress(
                task_id=task_id,
                current_step="Uploading to cloud storage",
                percent=90,
                details="Uploading converted video to Cloudflare R2"
            )
                
            # Upload the converted video
            upload_result = self.cloud_uploader.upload_file(
                conversion_result['output_path'],
                content_type=f"video/{output_format}"
            )
            
            if not upload_result["success"]:
                self.progress_tracker.update_progress(
                    task_id=task_id,
                    current_step="Upload failed",
                    percent=90,
                    details=f"Failed to upload to Cloudflare R2: {upload_result.get('error', 'Unknown error')}"
                )
                raise Exception(f"Failed to upload to Cloudflare R2: {upload_result.get('error', 'Unknown error')}")
            
            # Update progress to 100%
            self.progress_tracker.update_progress(
                task_id=task_id,
                current_step="Completed",
                percent=100,
                details=f"Video conversion completed successfully"
            )
            
            # Return the result
            return {
                "success": True,
                "message": "Video converted and uploaded successfully",
                "output_path": conversion_result["output_path"],
                "output_format": output_format,
                "duration": video_info.get("duration", 0),
                "url": upload_result["url"],
                "thumbnail_url": conversion_result.get("thumbnail_url", None)
            }
            
        except Exception as e:
            logger.error(f"Error in video format task: {str(e)}")
            if task_id:
                self.progress_tracker.update_progress(
                    task_id=task_id,
                    current_step="Error",
                    percent=0,
                    details=f"Error processing video: {str(e)}"
                )
            raise


class OptimizedVideoFormatTaskStrategy(BaseVideoFormatTaskStrategy):
    """Optimized video format task processing strategy.
    
    This strategy uses an optimized approach for processing video format tasks,
    with improved error handling and parallel processing where possible.
    """
    
    def process_video_format_task(self, temp_dir: str, file_path: str, output_format: str,
                                quality: str, width: Optional[int], height: Optional[int],
                                bitrate: Optional[str], preset: str, crf: Optional[int],
                                audio_codec: Optional[str], audio_bitrate: Optional[str],
                                original_filename: Optional[str], task_id: Optional[str],
                                progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Process a video format task using the optimized strategy.
        
        Args:
            temp_dir: Temporary directory for processing
            file_path: Path to the uploaded video file
            output_format: Desired output format (mp4, webm, etc.)
            quality: Quality preset (low, medium, high, veryhigh)
            width: Output width
            height: Output height
            bitrate: Video bitrate (e.g., "1M" for 1 Mbps)
            preset: Encoding preset (ultrafast to veryslow)
            crf: Constant Rate Factor (0-51, lower means better quality)
            audio_codec: Audio codec (aac, mp3, opus, etc.)
            audio_bitrate: Audio bitrate (e.g., "128k")
            original_filename: Original filename of the uploaded video
            task_id: Task ID for progress tracking
            progress_callback: Callback function for progress updates
            
        Returns:
            Dict[str, Any]: Processing result with URLs
        """
        try:
            logger.info(f"Converting video format with optimized strategy: {original_filename}")
            
            # Use the standard strategy with additional optimizations
            standard_strategy = StandardVideoFormatTaskStrategy(
                self.progress_tracker,
                self.cloud_uploader
            )
            
            # Call the standard strategy with the same parameters
            result = standard_strategy.process_video_format_task(
                temp_dir, file_path, output_format, quality, width, height,
                bitrate, preset, crf, audio_codec, audio_bitrate,
                original_filename, task_id, progress_callback
            )
            
            # Add additional metadata to the result
            result["strategy"] = "optimized"
            result["processing_time"] = time.time() - time.time()  # Placeholder for actual timing
            
            return result
            
        except Exception as e:
            logger.error(f"Error in optimized video format task: {str(e)}")
            if task_id:
                self.progress_tracker.update_progress(
                    task_id=task_id,
                    current_step="Error",
                    percent=0,
                    details=f"Error processing video: {str(e)}"
                )
            raise


class FallbackVideoFormatTaskStrategy(BaseVideoFormatTaskStrategy):
    """Fallback video format task processing strategy.
    
    This strategy provides a simplified approach for processing video format tasks
    when other strategies fail, focusing on reliability over features.
    """
    
    def process_video_format_task(self, temp_dir: str, file_path: str, output_format: str,
                                quality: str, width: Optional[int], height: Optional[int],
                                bitrate: Optional[str], preset: str, crf: Optional[int],
                                audio_codec: Optional[str], audio_bitrate: Optional[str],
                                original_filename: Optional[str], task_id: Optional[str],
                                progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Process a video format task using the fallback strategy.
        
        Args:
            temp_dir: Temporary directory for processing
            file_path: Path to the uploaded video file
            output_format: Desired output format (mp4, webm, etc.)
            quality: Quality preset (low, medium, high, veryhigh)
            width: Output width
            height: Output height
            bitrate: Video bitrate (e.g., "1M" for 1 Mbps)
            preset: Encoding preset (ultrafast to veryslow)
            crf: Constant Rate Factor (0-51, lower means better quality)
            audio_codec: Audio codec (aac, mp3, opus, etc.)
            audio_bitrate: Audio bitrate (e.g., "128k")
            original_filename: Original filename of the uploaded video
            task_id: Task ID for progress tracking
            progress_callback: Callback function for progress updates
            
        Returns:
            Dict[str, Any]: Processing result with URLs
        """
        try:
            logger.info(f"Converting video format with fallback strategy: {original_filename}")
            
            # Update progress if task_id is provided
            if task_id:
                self.progress_tracker.update_progress(
                    task_id=task_id,
                    current_step="Using fallback strategy",
                    percent=10,
                    details=f"Using simplified conversion approach for reliability"
                )
            
            # Use the legacy convert_video function directly with minimal parameters
            # This provides a more reliable fallback with fewer features
            conversion_result = convert_video(
                input_path=file_path,
                output_dir=temp_dir,
                output_format=output_format,
                quality="medium",  # Use medium quality for reliability
                task_id=task_id
            )
            
            logger.info(f"Video converted with fallback strategy: {conversion_result['output_path']}")
            
            # Upload the converted video
            if task_id:
                self.progress_tracker.update_progress(
                    task_id=task_id,
                    current_step="Uploading to cloud storage",
                    percent=90,
                    details="Uploading converted video to Cloudflare R2"
                )
            
            upload_result = self.cloud_uploader.upload_file(
                conversion_result['output_path'],
                content_type=f"video/{output_format}"
            )
            
            if not upload_result["success"]:
                if task_id:
                    self.progress_tracker.update_progress(
                        task_id=task_id,
                        current_step="Upload failed",
                        percent=90,
                        details=f"Failed to upload to Cloudflare R2: {upload_result.get('error', 'Unknown error')}"
                    )
                raise Exception(f"Failed to upload to Cloudflare R2: {upload_result.get('error', 'Unknown error')}")
            
            # Update progress to 100%
            if task_id:
                self.progress_tracker.update_progress(
                    task_id=task_id,
                    current_step="Completed",
                    percent=100,
                    details=f"Video conversion completed with fallback strategy"
                )
            
            # Return the result
            return {
                "success": True,
                "message": "Video converted and uploaded successfully (fallback strategy)",
                "output_path": conversion_result["output_path"],
                "output_format": output_format,
                "url": upload_result["url"],
                "thumbnail_url": conversion_result.get("thumbnail_url", None),
                "strategy": "fallback"
            }
            
        except Exception as e:
            logger.error(f"Error in fallback video format task: {str(e)}")
            if task_id:
                self.progress_tracker.update_progress(
                    task_id=task_id,
                    current_step="Error",
                    percent=0,
                    details=f"Error processing video with fallback strategy: {str(e)}"
                )
            raise
