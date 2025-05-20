import os
import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import (
    FastAPI,
    File,
    UploadFile,
    Query,
    HTTPException,
    BackgroundTasks,
    APIRouter,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.utils import (
    create_temp_directory,
    cleanup_temp_files,
)
from app.video_converter import get_supported_formats
from app.uploader import CloudflareR2Uploader
from app.task_queue import task_queue, TaskStatus

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app with enhanced documentation
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    contact={
        "name": "API Support",
        "url": "https://github.com/mrfansi/video-to-lottie",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/video-converter/docs",
    redoc_url="/video-converter/redoc",
    openapi_url="/video-converter/openapi.json",
)

# Create API router with prefix
router = APIRouter(prefix="/video-converter")


# Start the task queue on app startup
@app.on_event("startup")
def startup_event():
    # Register task handlers
    task_queue.register_handler("process_video", process_video_task)
    task_queue.register_handler("convert_video_format", convert_video_format_task)

    # Start the task queue
    task_queue.start()
    logger.info("Task queue started")


# Stop the task queue on app shutdown
@app.on_event("shutdown")
def shutdown_event():
    # Stop the task queue
    task_queue.stop()
    logger.info("Task queue stopped")


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create static directory if it doesn't exist
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

# Initialize R2 uploader
r2_uploader = CloudflareR2Uploader()


def process_video_task(
    temp_dir: str,
    file_path: str,
    fps: int,
    width: Optional[int] = None,  # Now optional
    height: Optional[int] = None,  # Now optional
    original_filename: Optional[str] = None,
    task_id: Optional[str] = None,  # Add task_id parameter for progress tracking
) -> Dict[str, Any]:
    """
    Background task to process a video and generate a Lottie animation

    Args:
        temp_dir (str): Temporary directory for processing
        file_path (str): Path to the uploaded video file
        fps (int): Frames per second for the animation
        width (int): Width of the animation
        height (int): Height of the animation
        original_filename (str): Original filename of the uploaded video
        task_id (str): Task ID for progress tracking

    Returns:
        Dict[str, Any]: Processing result with URLs
    """
    try:
        logger.info(f"Processing video in background: {original_filename}")

        # Define progress callback function for tracking progress
        def progress_callback(percent: int, details: Optional[str] = None):
            if task_id:
                # Map the percent to the appropriate step
                if percent < 20:
                    current_step = "Initializing"
                elif percent < 40:
                    current_step = "Extracting frames"
                elif percent < 60:
                    current_step = "Processing frames"
                elif percent < 80:
                    current_step = "Generating Lottie"
                elif percent < 100:
                    current_step = "Uploading files"
                else:
                    current_step = "Complete"

                task_queue.update_progress(
                    task_id=task_id,
                    current_step=current_step,
                    percent=percent,
                    details=details,
                )

        # Create output directory if it doesn't exist
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        # Initialize progress
        progress_callback(0, f"Preparing to process {original_filename}")

        # Import the VideoProcessor and parameter builder
        from app.infrastructure.video_processor import VideoProcessor
        from app.models.lottie_params import (
            VideoProcessingParamBuilder,
            VideoProcessingStrategy,
        )

        # Build the parameters for video processing
        params = (
            VideoProcessingParamBuilder()
            .with_file_path(file_path)
            .with_temp_dir(temp_dir)
            .with_fps(fps)
            .with_dimensions(width, height)
            .with_original_filename(original_filename)
            .with_strategy(VideoProcessingStrategy.STANDARD)
            .with_max_frames(100)
            .with_optimization(True, True)
            .with_task_id(task_id)
            .with_progress_callback(progress_callback)
            .build()
        )

        # Create the video processor with the R2 uploader
        processor = VideoProcessor(cloud_uploader=r2_uploader)

        # Process the video
        result = processor.process_video(params)

        # Update progress to complete
        progress_callback(100, "Video processing complete")

        # Return result with URLs
        return {
            "lottie_url": result.get("lottie_url"),
            "thumbnail_url": result.get("thumbnail_url"),
            "frame_count": result.get("frame_count"),
            "duration": result.get("duration"),
        }

    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        if task_id:
            task_queue.update_progress(
                task_id=task_id,
                current_step="Error",
                percent=0,
                details=f"Error processing video: {str(e)}",
            )
        raise ValueError(f"Failed to process video: {str(e)}")
        cleanup_temp_files(temp_dir)
        raise


@router.get("/", tags=["General"])
async def root():
    """
    Root endpoint - API health check

    Returns a simple message indicating the API is running.
    """
    return {"message": "Video to Lottie Conversion API", "status": "ok"}


@router.get("/test", response_class=HTMLResponse, tags=["UI"], include_in_schema=True)
async def test_page():
    """
    Serve the test upload page

    This endpoint serves an HTML page with a form for testing the video-to-lottie conversion.
    The page includes:
    - File upload form
    - Configuration options (FPS, width, height)
    - Real-time progress tracking
    - Lottie animation preview
    """
    test_html_path = Path("static/test_upload.html")
    if test_html_path.exists():
        return test_html_path.read_text()
    else:
        return "<html><body><h1>Test page not found</h1></body></html>"


@router.get(
    "/test-convert", response_class=HTMLResponse, tags=["UI"], include_in_schema=True
)
async def test_convert_page():
    """
    Serve the test video conversion page

    This endpoint serves an HTML page with a form for testing the video format conversion.
    The page includes:
    - File upload form
    - Format selection and quality options
    - Advanced configuration options
    - Real-time progress tracking
    - Video playback preview
    """
    test_html_path = Path("static/test_convert.html")
    if test_html_path.exists():
        return test_html_path.read_text()
    else:
        return "<html><body><h1>Test conversion page not found</h1></body></html>"


@router.post(
    "/upload", tags=["Conversion"], summary="Upload and convert video to Lottie"
)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(
        ..., description="Video file to convert (.mp4, .mov, .avi, .webm)"
    ),
    fps: int = Query(
        settings.DEFAULT_FPS,
        ge=1,
        le=30,
        description="Frames per second for the Lottie animation",
    ),
    width: int = Query(
        None,
        ge=100,
        le=2000,
        description="Width of the output Lottie animation (optional, uses source video width if not specified)",
    ),
    height: int = Query(
        None,
        ge=100,
        le=2000,
        description="Height of the output Lottie animation (optional, uses source video height if not specified)",
    ),
):
    """
    Upload a video file and convert it to a Lottie animation

    This endpoint accepts a video file and processes it asynchronously to create a Lottie animation.
    The process includes:
    1. Extracting frames from the video
    2. Converting frames to SVG paths using OpenCV
    3. Generating a Lottie JSON animation
    4. Uploading the results to Cloudflare R2 with a custom domain URL

    The endpoint returns a task ID and status endpoint that can be used to track the progress of the conversion.

    When the task is complete, the status endpoint will return URLs to the Lottie animation and thumbnail.
    """
    try:
        # Validate file type
        filename = file.filename
        file_extension = os.path.splitext(filename)[1].lower()

        if file_extension not in [".mp4", ".mov", ".avi", ".webm"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only .mp4, .mov, .avi, and .webm files are supported.",
            )

        # Create temporary directory for processing
        temp_dir = create_temp_directory()
        logger.info(f"Created temporary directory: {temp_dir}")

        # Save uploaded file
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        logger.info(f"Saved uploaded file to {file_path}")

        # Generate a unique task ID
        task_id = str(uuid.uuid4())

        # Add task to queue for background processing
        task = task_queue.add_task(
            task_id=task_id,
            task_type="process_video",
            params={
                "temp_dir": temp_dir,
                "file_path": file_path,
                "fps": fps,
                "width": width,
                "height": height,
                "original_filename": filename,
                "task_id": task_id,  # Pass the task_id to the process function
            },
        )

        logger.info(f"Added video processing task to queue: {task_id}")

        # Return task ID for status tracking
        return {
            "task_id": task_id,
            "status": task.status.value,
            "message": "Video processing started in the background",
            "status_endpoint": f"/video-converter/tasks/{task_id}",
        }

    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", tags=["Tasks"], summary="Get task status")
async def get_task_status(task_id: str):
    """
    Get the status of a video processing task

    This endpoint returns the current status of a video processing task, including:
    - Status (pending, processing, completed, failed)
    - Progress information (current step, percent complete, details)
    - Result URLs when the task is complete
    - Error information if the task failed

    Use this endpoint to track the progress of a video conversion task initiated with the `/upload` endpoint.

    Parameters:
    - task_id: The unique identifier for the task

    Returns:
    - Task status object with progress information and results when complete
    """
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Create response based on task status
    response = {
        "task_id": task.id,
        "status": task.status.value,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "progress": task.progress,  # Include progress information
    }

    # Add error if task failed
    if task.status == TaskStatus.FAILED and task.error:
        response["error"] = task.error

    # Add result if task completed
    if task.status == TaskStatus.COMPLETED and task.result:
        response["result"] = task.result

    return response


def convert_video_format_task(
    temp_dir: str,
    file_path: str,
    output_format: str,
    quality: str = "medium",
    width: Optional[int] = None,
    height: Optional[int] = None,
    bitrate: Optional[str] = None,
    preset: str = "medium",
    crf: Optional[int] = None,
    audio_codec: Optional[str] = None,
    audio_bitrate: Optional[str] = None,
    original_filename: Optional[str] = None,
    task_id: Optional[str] = None,  # Add task_id parameter for progress tracking
) -> Dict[str, Any]:
    """
    Background task to convert a video from one format to another with optimization

    Args:
        temp_dir (str): Temporary directory for processing
        file_path (str): Path to the uploaded video file
        output_format (str): Desired output format (mp4, webm, etc.)
        quality (str): Quality preset (low, medium, high, veryhigh)
        width (int, optional): Output width
        height (int, optional): Output height
        bitrate (str, optional): Video bitrate (e.g., "1M" for 1 Mbps)
        preset (str): Encoding preset (ultrafast to veryslow)
        crf (int, optional): Constant Rate Factor (0-51, lower means better quality)
        audio_codec (str, optional): Audio codec (aac, mp3, opus, etc.)
        audio_bitrate (str, optional): Audio bitrate (e.g., "128k")
        original_filename (str): Original filename of the uploaded video
        task_id (str, optional): Task ID for progress tracking

    Returns:
        Dict[str, Any]: Processing result with URLs
    """
    try:
        # Import the necessary modules
        from app.infrastructure.video_format_task import VideoFormatTaskProcessor
        from app.models.video_format_params import VideoFormatTaskParamBuilder

        logger.info(f"Converting video format in background: {original_filename}")

        # Create parameter object using builder pattern
        params_builder = VideoFormatTaskParamBuilder()
        params_builder.with_temp_dir(temp_dir)
        params_builder.with_file_path(file_path)
        params_builder.with_output_format(output_format)
        params_builder.with_quality(quality)

        if width is not None and height is not None:
            params_builder.with_dimensions(width, height)

        if bitrate is not None:
            params_builder.with_bitrate(bitrate)

        if preset is not None:
            params_builder.with_preset(preset)

        if crf is not None:
            params_builder.with_crf(crf)

        if audio_codec is not None:
            params_builder.with_audio_codec(audio_codec)

        if audio_bitrate is not None:
            params_builder.with_audio_bitrate(audio_bitrate)

        if original_filename is not None:
            params_builder.with_original_filename(original_filename)

        if task_id is not None:
            params_builder.with_task_id(task_id)

        # Build the parameters
        params = params_builder.build()

        # Create the processor and process the task
        processor = VideoFormatTaskProcessor()
        result = processor.process_video_format_task(
            temp_dir=params.temp_dir,
            file_path=params.file_path,
            output_format=params.output_format,
            quality=params.quality,
            width=params.width,
            height=params.height,
            bitrate=params.bitrate,
            preset=params.preset,
            crf=params.crf,
            audio_codec=params.audio_codec,
            audio_bitrate=params.audio_bitrate,
            original_filename=params.original_filename,
            task_id=params.task_id,
        )

        return result

    except Exception as e:
        logger.error(f"Error in video format task: {str(e)}")
        if task_id:
            task_queue.update_progress(
                task_id=task_id,
                current_step="Error",
                percent=0,
                details=f"Error processing video: {str(e)}",
            )
        # Clean up temporary files on error
        cleanup_temp_files(temp_dir)
        raise


@router.post(
    "/convert",
    tags=["Conversion"],
    summary="Convert video to another format with optimization",
)
async def convert_video_format(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(
        ...,
        description="Video file to convert (.mp4, .mov, .avi, .webm, .mkv, .flv, .wmv, .m4v)",
    ),
    output_format: str = Query(
        ..., description="Output format (mp4, webm, mov, avi, mkv, flv)"
    ),
    quality: str = Query(
        "medium", description="Quality preset (low, medium, high, veryhigh)"
    ),
    width: Optional[int] = Query(
        None,
        description="Width of the output video (maintains aspect ratio if only width or height is specified)",
    ),
    height: Optional[int] = Query(None, description="Height of the output video"),
    bitrate: Optional[str] = Query(
        None, description="Video bitrate (e.g., '1M' for 1 Mbps)"
    ),
    preset: str = Query(
        "medium",
        description="Encoding preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)",
    ),
    crf: Optional[int] = Query(
        None,
        ge=0,
        le=51,
        description="Constant Rate Factor (0-51, lower means better quality)",
    ),
    audio_codec: Optional[str] = Query(
        None, description="Audio codec (aac, mp3, opus, etc.)"
    ),
    audio_bitrate: Optional[str] = Query(
        None, description="Audio bitrate (e.g., '128k')"
    ),
):
    """
    Upload a video file and convert it to another format with optimization

    This endpoint accepts a video file and processes it asynchronously to convert it to another format.
    The process includes:
    1. Analyzing the input video properties
    2. Converting the video to the specified format with optimization options
    3. Uploading the results to Cloudflare R2 with a custom domain URL
    4. Generating a thumbnail preview

    The endpoint returns a task ID and status endpoint that can be used to track the progress of the conversion.

    When the task is complete, the status endpoint will return URLs to the converted video and thumbnail.

    Available quality presets:
    - low: Smaller file size, lower quality (CRF 28)
    - medium: Balanced file size and quality (CRF 23)
    - high: Higher quality, larger file size (CRF 18)
    - veryhigh: Best quality, largest file size (CRF 12)

    Encoding presets affect encoding speed and compression efficiency:
    - ultrafast: Fastest encoding, lowest compression efficiency
    - medium: Balanced encoding speed and compression
    - veryslow: Slowest encoding, best compression efficiency
    """
    try:
        # Validate file type
        filename = file.filename
        file_extension = os.path.splitext(filename)[1].lower()

        # Get supported formats
        formats = get_supported_formats()

        if file_extension not in formats["input_formats"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Supported formats: {', '.join(formats['input_formats'])}",
            )

        if output_format not in formats["output_formats"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid output format. Supported formats: {', '.join(formats['output_formats'])}",
            )

        if quality not in formats["quality_presets"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid quality preset. Supported presets: {', '.join(formats['quality_presets'])}",
            )

        if preset not in formats["encoding_presets"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid encoding preset. Supported presets: {', '.join(formats['encoding_presets'])}",
            )

        # Create temporary directory for processing
        temp_dir = create_temp_directory()
        logger.info(f"Created temporary directory: {temp_dir}")

        # Save uploaded file
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        logger.info(f"Saved uploaded file to {file_path}")

        # Generate a unique task ID
        task_id = str(uuid.uuid4())

        # Add task to queue for background processing
        task = task_queue.add_task(
            task_id=task_id,
            task_type="convert_video_format",
            params={
                "temp_dir": temp_dir,
                "file_path": file_path,
                "output_format": output_format,
                "quality": quality,
                "width": width,
                "height": height,
                "bitrate": bitrate,
                "preset": preset,
                "crf": crf,
                "audio_codec": audio_codec,
                "audio_bitrate": audio_bitrate,
                "original_filename": filename,
                "task_id": task_id,  # Pass the task_id to the process function
            },
        )

        logger.info(f"Added video conversion task to queue: {task_id}")

        # Return task ID for status tracking
        return {
            "task_id": task_id,
            "status": task.status.value,
            "message": f"Video conversion to {output_format} started in the background",
            "status_endpoint": f"/video-converter/tasks/{task_id}",
        }

    except Exception as e:
        logger.error(f"Error processing video conversion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/formats", tags=["Conversion"], summary="Get supported video formats and options"
)
async def get_formats():
    """
    Get a list of supported video formats and conversion options

    Returns information about:
    - Supported input formats
    - Supported output formats
    - Available quality presets
    - Available encoding presets
    """
    return get_supported_formats()


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    # Check R2 connection
    r2_status = "ok" if r2_uploader.check_bucket_exists() else "error"

    return {"status": "ok", "components": {"api": "ok", "r2_storage": r2_status}}


# Include the router in the app
app.include_router(router)


def start_app():
    """
    Entry point for the application when installed as a package.
    Used by the 'start' script defined in pyproject.toml.
    """
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)


def start_dev():
    """
    Entry point for development mode with auto-reload.
    Used by the 'dev' script defined in pyproject.toml.
    """
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start_dev()
