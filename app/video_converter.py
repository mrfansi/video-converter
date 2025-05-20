import os
import time
import ffmpeg
import logging
from typing import Dict, Any, Optional, List, Callable


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_video(
    input_path: str,
    output_dir: str,
    output_format: str,
    quality: str = "medium",
    width: Optional[int] = None,
    height: Optional[int] = None,
    bitrate: Optional[str] = None,
    preset: str = "medium",
    crf: Optional[int] = None,
    audio_codec: Optional[str] = None,
    audio_bitrate: Optional[str] = None,
    task_id: Optional[str] = None,
    progress_callback: Optional[
        Callable[[int, str, Optional[str], Optional[str]], None]
    ] = None,
) -> Dict[str, Any]:
    """
    Convert a video file to another format with optimization options

    Args:
        input_path (str): Path to the input video file
        output_dir (str): Directory to save the output video
        output_format (str): Output format (mp4, webm, mov, avi, etc.)
        quality (str): Quality preset (low, medium, high, veryhigh)
        width (int, optional): Output width (maintains aspect ratio if only width or height is specified)
        height (int, optional): Output height
        bitrate (str, optional): Video bitrate (e.g., "1M" for 1 Mbps)
        preset (str): Encoding preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
        crf (int, optional): Constant Rate Factor (0-51, lower means better quality)
        audio_codec (str, optional): Audio codec (aac, mp3, opus, etc.)
        audio_bitrate (str, optional): Audio bitrate (e.g., "128k")
        task_id (str, optional): Task ID for progress tracking
        progress_callback (callable, optional): Callback function for progress updates

    Returns:
        Dict[str, Any]: Dictionary with output file information
    """
    try:
        # Generate output filename
        timestamp = int(time.time())
        output_filename = f"converted_{timestamp}.{output_format}"
        output_path = os.path.join(output_dir, output_filename)

        # Set up ffmpeg input
        input_stream = ffmpeg.input(input_path)

        # Prepare video parameters
        video_params: Dict[str, Any] = {}

        # Map quality presets to CRF values if not explicitly provided
        if crf is None:
            quality_to_crf = {"low": 28, "medium": 23, "high": 18, "veryhigh": 12}
            crf = quality_to_crf.get(quality.lower(), 23)
            video_params["crf"] = crf
        else:
            video_params["crf"] = crf

        # Set preset
        video_params["preset"] = preset

        # Set bitrate if provided
        if bitrate:
            video_params["b:v"] = bitrate

        # Determine video codec based on output format
        format_to_codec = {
            "mp4": "libx264",
            "webm": "libvpx-vp9",
            "mov": "libx264",
            "avi": "libx264",
            "mkv": "libx264",
            "flv": "flv",
        }
        video_codec = format_to_codec.get(output_format.lower(), "libx264")

        # Determine audio codec if not specified
        if audio_codec is None:
            format_to_audio = {
                "mp4": "aac",
                "webm": "libopus",
                "mov": "aac",
                "avi": "aac",
                "mkv": "aac",
                "flv": "aac",
            }
            audio_codec = format_to_audio.get(output_format.lower(), "aac")

        # Set up audio parameters
        audio_params = {"c:a": audio_codec}
        if audio_bitrate:
            audio_params["b:a"] = audio_bitrate

        # Apply scaling if width or height is specified
        if width or height:
            scale_params = {}
            if width:
                scale_params["width"] = width
            if height:
                scale_params["height"] = height

            # If only one dimension is specified, maintain aspect ratio
            if width and not height:
                scale_params["height"] = -1
            elif height and not width:
                scale_params["width"] = -1

            video_stream = input_stream.video.filter("scale", **scale_params)
        else:
            video_stream = input_stream.video

        # Set up progress tracking
        total_duration = None
        if task_id and progress_callback:
            # Get video duration
            probe = ffmpeg.probe(input_path)
            video_info = next(s for s in probe["streams"] if s["codec_type"] == "video")
            total_duration = float(video_info.get("duration", 0))

        # Build the output with all parameters
        output_args = {"c:v": video_codec, **video_params, **audio_params}

        # Create output stream
        output = ffmpeg.output(
            video_stream, input_stream.audio, output_path, **output_args
        )

        # Run the conversion
        if task_id and progress_callback and total_duration:
            # Custom progress tracking
            cmd = ffmpeg.compile(output, overwrite_output=True)
            process = ffmpeg.run_async(cmd, pipe_stdout=True, pipe_stderr=True)

            # Process stderr to track progress
            last_progress = 0
            while process.poll() is None:
                stderr_line = process.stderr.readline().decode("utf8", errors="replace")
                if "time=" in stderr_line:
                    time_str = stderr_line.split("time=")[1].split()[0]
                    # Convert HH:MM:SS.MS to seconds
                    parts = time_str.split(":")
                    if len(parts) == 3:
                        hours, minutes, seconds = parts
                        seconds = float(seconds)
                        current_time = (
                            float(hours) * 3600 + float(minutes) * 60 + seconds
                        )
                        progress = min(int((current_time / total_duration) * 100), 100)

                        # Only update if progress has changed significantly
                        if progress - last_progress >= 5:
                            progress_callback(
                                progress,
                                "Converting video",
                                task_id,
                                f"Processing: {progress}% complete",
                            )
                            last_progress = progress
        else:
            # Simple run without progress tracking
            output = output.overwrite_output()
            output.run(quiet=True)

        # Return information about the converted file
        file_stats = os.stat(output_path)
        return {
            "output_path": output_path,
            "format": output_format,
            "size_bytes": file_stats.st_size,
            "duration": total_duration if total_duration else None,
        }

    except ffmpeg.Error as e:
        error_message = e.stderr.decode() if hasattr(e, "stderr") else str(e)
        logger.error(f"Error converting video: {error_message}")
        raise RuntimeError(f"Failed to convert video: {error_message}")
    except Exception as e:
        logger.error(f"Unexpected error converting video: {str(e)}")
        raise


def get_video_info(video_path: str) -> Dict[str, Any]:
    """
    Get information about a video file using ffprobe

    Args:
        video_path (str): Path to the video file

    Returns:
        Dict[str, Any]: Dictionary with video information
    """
    try:
        # Run ffprobe
        probe = ffmpeg.probe(video_path)

        # Extract video stream information
        video_info = next(
            (stream for stream in probe["streams"] if stream["codec_type"] == "video"),
            None,
        )
        audio_info = next(
            (stream for stream in probe["streams"] if stream["codec_type"] == "audio"),
            None,
        )

        if not video_info:
            raise ValueError("No video stream found")

        # Extract relevant information
        info = {
            "format": probe["format"]["format_name"],
            "duration": float(probe["format"]["duration"]),
            "size_bytes": int(probe["format"]["size"]),
            "bitrate": int(probe["format"]["bit_rate"]),
            "video": {
                "codec": video_info["codec_name"],
                "width": int(video_info["width"]),
                "height": int(video_info["height"]),
                "fps": eval(video_info.get("avg_frame_rate", "0/1")),
            },
        }

        # Add audio information if available
        if audio_info:
            info["audio"] = {
                "codec": audio_info["codec_name"],
                "channels": int(audio_info.get("channels", 0)),
                "sample_rate": int(audio_info.get("sample_rate", 0)),
                "bitrate": (
                    int(audio_info.get("bit_rate", 0))
                    if "bit_rate" in audio_info
                    else None
                ),
            }

        return info

    except ffmpeg.Error as e:
        error_message = e.stderr.decode() if hasattr(e, "stderr") else str(e)
        logger.error(f"Error getting video info: {error_message}")
        raise RuntimeError(f"Failed to get video info: {error_message}")
    except Exception as e:
        logger.error(f"Unexpected error getting video info: {str(e)}")
        raise


def get_supported_formats() -> Dict[str, List[str]]:
    """
    Get a list of supported input and output formats

    Returns:
        Dict[str, List[str]]: Dictionary with input and output formats
    """
    return {
        "input_formats": [
            ".mp4",
            ".mov",
            ".avi",
            ".webm",
            ".mkv",
            ".flv",
            ".wmv",
            ".m4v",
        ],
        "output_formats": ["mp4", "webm", "mov", "avi", "mkv", "flv"],
        "quality_presets": ["low", "medium", "high", "veryhigh"],
        "encoding_presets": [
            "ultrafast",
            "superfast",
            "veryfast",
            "faster",
            "fast",
            "medium",
            "slow",
            "slower",
            "veryslow",
        ],
    }
