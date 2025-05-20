import os
import time
import uuid
import logging
import tempfile
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, Form, Query, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.utils import create_temp_directory, extract_frames, prepare_frame_for_tracing, cleanup_temp_files
from app.video_converter import convert_video, get_video_info, get_supported_formats
from app.lottie import LottieGeneratorFacade
from app.uploader import CloudflareR2Uploader
from app.thumbnail_generator import generate_thumbnail_from_frame, upload_thumbnail
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
from fastapi import APIRouter
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
    width: int = None,  # Now optional
    height: int = None,  # Now optional
    original_filename: str = None,
    task_id: str = None  # Add task_id parameter for progress tracking
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
        
    Returns:
        Dict[str, Any]: Processing result with URLs
    """
    try:
        logger.info(f"Processing video in background: {original_filename}")
        
        # Define total steps for progress tracking
        total_steps = 5  # Initialize, extract, trace, generate, upload
        current_step = 0
        
        # Update progress if task_id is provided
        if task_id:
            task_queue.update_progress(
                task_id=task_id,
                current_step="Initializing",
                total_steps=total_steps,
                completed_steps=current_step,
                percent=0,
                details=f"Preparing to process {original_filename}"
            )
        
        # Use data folder for frames and SVGs instead of temp_dir
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        frames_dir = os.path.join(data_dir, "frames")
        svg_dir = os.path.join(data_dir, "svg")
        os.makedirs(frames_dir, exist_ok=True)
        os.makedirs(svg_dir, exist_ok=True)
        
        # Create a unique subfolder for this video processing task
        task_timestamp = int(time.time())
        frames_dir = os.path.join(frames_dir, str(task_timestamp))
        svg_dir = os.path.join(svg_dir, str(task_timestamp))
        os.makedirs(frames_dir, exist_ok=True)
        os.makedirs(svg_dir, exist_ok=True)
        
        # Get original video dimensions
        video_info = get_video_info(file_path)
        source_width = video_info['video']['width']
        source_height = video_info['video']['height']
        
        # Use source dimensions if width/height not specified
        if width is None or height is None:
            width = source_width
            height = source_height
            logger.info(f"Using source video dimensions: {width}x{height}")
            
        # Step 1: Extract frames from video
        current_step += 1
        if task_id:
            task_queue.update_progress(
                task_id=task_id,
                current_step="Extracting frames",
                completed_steps=current_step,
                details=f"Extracting frames from video at {fps} fps"
            )
            
        frame_paths = extract_frames(file_path, frames_dir, fps=fps, width=width, height=height)
        logger.info(f"Extracted {len(frame_paths)} frames from video")
        
        # Step 2: Process frames to generate SVG files
        current_step += 1
        if task_id:
            task_queue.update_progress(
                task_id=task_id,
                current_step="Tracing frames",
                completed_steps=current_step,
                details=f"Converting {len(frame_paths)} frames to vector graphics"
            )
            
        svg_paths = []
        total_frames = len(frame_paths)
        
        for i, frame_path in enumerate(frame_paths):
            # Update progress for each frame if task_id is provided
            if task_id and i % max(1, total_frames // 10) == 0:  # Update every ~10% of frames
                frame_percent = int((i / total_frames) * 100)
                sub_step_percent = current_step * 20 + (frame_percent // 5)  # Scale to overall progress
                task_queue.update_progress(
                    task_id=task_id,
                    current_step="Tracing frames",
                    percent=sub_step_percent,
                    details=f"Processing frame {i+1}/{total_frames} ({frame_percent}%)"
                )
                
            # Prepare frame for tracing
            prepared_frame = prepare_frame_for_tracing(frame_path)
            
            # Trace PNG to SVG using the Lottie generator facade
            lottie_facade = LottieGeneratorFacade()
            svg_path = lottie_facade.trace_png_to_svg(prepared_frame, svg_dir)
            svg_paths.append(svg_path)
        
        logger.info(f"Generated {len(svg_paths)} SVG files")
        
        # Step 3: Create Lottie animation directly from SVG files
        current_step += 1
        if task_id:
            task_queue.update_progress(
                task_id=task_id,
                current_step="Creating Lottie animation",
                completed_steps=current_step,
                percent=60,
                details=f"Generating Lottie animation from {len(svg_paths)} SVG files"
            )
        
        # Create Lottie animation directly from SVG files using the facade
        lottie_facade = LottieGeneratorFacade()
        lottie_filename = f"output_{int(time.time())}.json"
        lottie_path = os.path.join(temp_dir, lottie_filename)
        
        # Use the facade to create and save the Lottie animation in one step
        lottie_path = lottie_facade.create_lottie_from_svgs(
            svg_paths=svg_paths,
            output_path=lottie_path,
            fps=fps,
            width=width,
            height=height,
            max_frames=100,
            optimize=True,
            compress=True
        )
        logger.info(f"Saved Lottie JSON to {lottie_path}")
        
        # Step 5: Upload to Cloudflare R2
        current_step += 1
        if task_id:
            task_queue.update_progress(
                task_id=task_id,
                current_step="Uploading to cloud storage",
                completed_steps=current_step,
                percent=90,
                details="Uploading Lottie animation to Cloudflare R2"
            )
            
        upload_result = r2_uploader.upload_file(lottie_path)
        
        if not upload_result["success"]:
            if task_id:
                task_queue.update_progress(
                    task_id=task_id,
                    current_step="Upload failed",
                    percent=90,
                    details=f"Failed to upload to Cloudflare R2: {upload_result.get('error', 'Unknown error')}"
                )
            raise Exception(f"Failed to upload to Cloudflare R2: {upload_result.get('error', 'Unknown error')}")
        
        # Generate and upload a thumbnail from the first frame if available
        thumbnail_url = None
        if frame_paths and len(frame_paths) > 0:
            try:
                if task_id:
                    task_queue.update_progress(
                        task_id=task_id,
                        current_step="Generating thumbnail",
                        percent=95,
                        details="Creating and uploading thumbnail preview"
                    )
                    
                # Use the first frame for the thumbnail
                first_frame = frame_paths[0]
                thumbnail_path = generate_thumbnail_from_frame(
                    frame_path=first_frame,
                    output_dir=temp_dir,
                    source_dimensions=(width, height),  # Use source video dimensions
                    maintain_aspect_ratio=True
                )
                
                # Upload the thumbnail with a related object key
                lottie_key = upload_result["object_key"]
                thumbnail_key = lottie_key.replace(".json", ".png")
                
                thumbnail_result = r2_uploader.upload_file(
                    thumbnail_path, 
                    content_type="image/png",
                    custom_key=thumbnail_key
                )
                
                if thumbnail_result["success"]:
                    thumbnail_url = thumbnail_result["url"]
                    logger.info(f"Thumbnail uploaded successfully: {thumbnail_url}")
            except Exception as e:
                # Don't fail the whole request if thumbnail generation fails
                logger.warning(f"Thumbnail generation failed: {str(e)}")
        
        # Final step: Cleanup and completion
        if task_id:
            task_queue.update_progress(
                task_id=task_id,
                current_step="Completing task",
                percent=100,
                details="Processing complete, cleaning up temporary files"
            )
            
        # Clean up temporary files
        cleanup_temp_files(temp_dir)
        
        # Return success response with URLs
        response = {"url": upload_result["url"]}
        
        # Add thumbnail URL if available
        if thumbnail_url:
            response["thumbnail_url"] = thumbnail_url
            
        return response
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        # Clean up temporary files on error
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

@router.get("/test-convert", response_class=HTMLResponse, tags=["UI"], include_in_schema=True)
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

@router.post("/upload", tags=["Conversion"], summary="Upload and convert video to Lottie")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Video file to convert (.mp4, .mov, .avi, .webm)"),
    fps: int = Query(settings.DEFAULT_FPS, ge=1, le=30, description="Frames per second for the Lottie animation"),
    width: int = Query(None, ge=100, le=2000, description="Width of the output Lottie animation (optional, uses source video width if not specified)"),
    height: int = Query(None, ge=100, le=2000, description="Height of the output Lottie animation (optional, uses source video height if not specified)")
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
                detail="Invalid file type. Only .mp4, .mov, .avi, and .webm files are supported."
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
                "task_id": task_id  # Pass the task_id to the process function
            }
        )
        
        logger.info(f"Added video processing task to queue: {task_id}")
        
        # Return task ID for status tracking
        return {
            "task_id": task_id,
            "status": task.status.value,
            "message": "Video processing started in the background",
            "status_endpoint": f"/video-converter/tasks/{task_id}"
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
        "progress": task.progress  # Include progress information
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
    width: int = None,
    height: int = None,
    bitrate: str = None,
    preset: str = "medium",
    crf: int = None,
    audio_codec: str = None,
    audio_bitrate: str = None,
    original_filename: str = None,
    task_id: str = None  # Add task_id parameter for progress tracking
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
        logger.info(f"Converting video format in background: {original_filename}")
        
        # Define total steps for progress tracking
        total_steps = 3  # Initialize, convert, upload
        current_step = 0
        
        # Update progress if task_id is provided
        if task_id:
            task_queue.update_progress(
                task_id=task_id,
                current_step="Initializing",
                total_steps=total_steps,
                completed_steps=current_step,
                percent=0,
                details=f"Preparing to convert {original_filename} to {output_format}"
            )
        
        # Step 1: Get video information
        current_step += 1
        if task_id:
            task_queue.update_progress(
                task_id=task_id,
                current_step="Analyzing video",
                completed_steps=current_step,
                percent=10,
                details=f"Analyzing video properties"
            )
            
        video_info = get_video_info(file_path)
        logger.info(f"Video info: {video_info}")
        
        # Step 2: Convert video
        current_step += 1
        if task_id:
            task_queue.update_progress(
                task_id=task_id,
                current_step="Converting video",
                completed_steps=current_step,
                percent=20,
                details=f"Converting video to {output_format}"
            )
            
        # Define progress callback function
        def progress_update(task_id, current_step, percent, details):
            task_queue.update_progress(
                task_id=task_id,
                current_step=current_step,
                percent=20 + int(percent * 0.7),  # Scale to 20-90% of overall progress
                details=details
            )
        
        # Convert the video
        conversion_result = convert_video(
            input_path=file_path,
            output_dir=temp_dir,
            output_format=output_format,
            quality=quality,
            width=width,
            height=height,
            bitrate=bitrate,
            preset=preset,
            crf=crf,
            audio_codec=audio_codec,
            audio_bitrate=audio_bitrate,
            task_id=task_id,
            progress_callback=progress_update if task_id else None
        )
        
        logger.info(f"Video converted successfully: {conversion_result['output_path']}")
        
        # Step 3: Upload to Cloudflare R2
        current_step += 1
        if task_id:
            task_queue.update_progress(
                task_id=task_id,
                current_step="Uploading to cloud storage",
                completed_steps=current_step,
                percent=90,
                details="Uploading converted video to Cloudflare R2"
            )
            
        # Upload the converted video
        upload_result = r2_uploader.upload_file(
            conversion_result['output_path'],
            content_type=f"video/{output_format}"
        )
        
        if not upload_result["success"]:
            if task_id:
                task_queue.update_progress(
                    task_id=task_id,
                    current_step="Upload failed",
                    percent=90,
                    details=f"Failed to upload to Cloudflare R2: {upload_result.get('error', 'Unknown error')}"
                )
            raise Exception(f"Failed to upload to Cloudflare R2: {upload_result.get('error', 'Unknown error')}")
        
        # Generate and upload a thumbnail
        thumbnail_url = None
        try:
            if task_id:
                task_queue.update_progress(
                    task_id=task_id,
                    current_step="Generating thumbnail",
                    percent=95,
                    details="Creating and uploading thumbnail preview"
                )
                
            # Extract a frame for the thumbnail
            frames_dir = os.path.join(temp_dir, "frames")
            os.makedirs(frames_dir, exist_ok=True)
            
            # Extract just one frame for thumbnail
            frame_paths = extract_frames(
                file_path, 
                frames_dir, 
                fps=1,  # Just extract one frame
                width=settings.DEFAULT_WIDTH,
                height=settings.DEFAULT_HEIGHT
            )
            
            if frame_paths and len(frame_paths) > 0:
                # Use the first frame for the thumbnail
                first_frame = frame_paths[0]
                thumbnail_path = generate_thumbnail_from_frame(
                    frame_path=first_frame,
                    output_dir=temp_dir,
                    source_dimensions=(width, height),  # Use source video dimensions
                    maintain_aspect_ratio=True
                )
                
                # Upload the thumbnail with a related object key
                video_key = upload_result["object_key"]
                thumbnail_key = video_key.replace(f".{output_format}", ".png")
                
                thumbnail_result = r2_uploader.upload_file(
                    thumbnail_path, 
                    content_type="image/png",
                    custom_key=thumbnail_key
                )
                
                if thumbnail_result["success"]:
                    thumbnail_url = thumbnail_result["url"]
                    logger.info(f"Thumbnail uploaded successfully: {thumbnail_url}")
        except Exception as e:
            # Don't fail the whole request if thumbnail generation fails
            logger.warning(f"Thumbnail generation failed: {str(e)}")
        
        # Final step: Cleanup and completion
        if task_id:
            task_queue.update_progress(
                task_id=task_id,
                current_step="Completing task",
                percent=100,
                details="Processing complete, cleaning up temporary files"
            )
            
        # Clean up temporary files
        cleanup_temp_files(temp_dir)
        
        # Return success response with URLs
        response = {
            "url": upload_result["url"],
            "format": output_format,
            "size_bytes": conversion_result["size_bytes"],
            "duration": conversion_result["duration"]
        }
        
        # Add thumbnail URL if available
        if thumbnail_url:
            response["thumbnail_url"] = thumbnail_url
            
        return response
        
    except Exception as e:
        logger.error(f"Error converting video: {str(e)}")
        # Clean up temporary files on error
        cleanup_temp_files(temp_dir)
        raise

@router.post("/convert", tags=["Conversion"], summary="Convert video to another format with optimization")
async def convert_video_format(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Video file to convert (.mp4, .mov, .avi, .webm, .mkv, .flv, .wmv, .m4v)"),
    output_format: str = Query(..., description="Output format (mp4, webm, mov, avi, mkv, flv)"),
    quality: str = Query("medium", description="Quality preset (low, medium, high, veryhigh)"),
    width: Optional[int] = Query(None, description="Width of the output video (maintains aspect ratio if only width or height is specified)"),
    height: Optional[int] = Query(None, description="Height of the output video"),
    bitrate: Optional[str] = Query(None, description="Video bitrate (e.g., '1M' for 1 Mbps)"),
    preset: str = Query("medium", description="Encoding preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)"),
    crf: Optional[int] = Query(None, ge=0, le=51, description="Constant Rate Factor (0-51, lower means better quality)"),
    audio_codec: Optional[str] = Query(None, description="Audio codec (aac, mp3, opus, etc.)"),
    audio_bitrate: Optional[str] = Query(None, description="Audio bitrate (e.g., '128k')")
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
                detail=f"Invalid file type. Supported formats: {', '.join(formats['input_formats'])}"
            )
        
        if output_format not in formats["output_formats"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid output format. Supported formats: {', '.join(formats['output_formats'])}"
            )
        
        if quality not in formats["quality_presets"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid quality preset. Supported presets: {', '.join(formats['quality_presets'])}"
            )
        
        if preset not in formats["encoding_presets"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid encoding preset. Supported presets: {', '.join(formats['encoding_presets'])}"
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
                "task_id": task_id  # Pass the task_id to the process function
            }
        )
        
        logger.info(f"Added video conversion task to queue: {task_id}")
        
        # Return task ID for status tracking
        return {
            "task_id": task_id,
            "status": task.status.value,
            "message": f"Video conversion to {output_format} started in the background",
            "status_endpoint": f"/video-converter/tasks/{task_id}"
        }
        
    except Exception as e:
        logger.error(f"Error processing video conversion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/formats", tags=["Conversion"], summary="Get supported video formats and options")
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
    
    return {
        "status": "ok",
        "components": {
            "api": "ok",
            "r2_storage": r2_status
        }
    }

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
