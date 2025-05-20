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
from app.lottie_generator import trace_png_to_svg, parse_svg_to_paths, create_lottie_animation, save_lottie_json
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
)

# Start the task queue on app startup
@app.on_event("startup")
def startup_event():
    # Register task handlers
    task_queue.register_handler("process_video", process_video_task)
    
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
    width: int,
    height: int,
    original_filename: str,
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
        
        # Create subdirectories for frames and SVGs
        frames_dir = os.path.join(temp_dir, "frames")
        svg_dir = os.path.join(temp_dir, "svg")
        os.makedirs(frames_dir, exist_ok=True)
        os.makedirs(svg_dir, exist_ok=True)
        
        # Step 1: Extract frames from video
        current_step += 1
        if task_id:
            task_queue.update_progress(
                task_id=task_id,
                current_step="Extracting frames",
                completed_steps=current_step,
                details=f"Extracting frames from video at {fps} fps"
            )
            
        frame_paths = extract_frames(file_path, frames_dir, fps)
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
            
            # Trace PNG to SVG
            svg_path = trace_png_to_svg(prepared_frame, svg_dir)
            svg_paths.append(svg_path)
        
        logger.info(f"Generated {len(svg_paths)} SVG files")
        
        # Step 3: Parse SVG files to extract paths
        current_step += 1
        if task_id:
            task_queue.update_progress(
                task_id=task_id,
                current_step="Parsing SVG files",
                completed_steps=current_step,
                percent=60,
                details=f"Extracting vector paths from {len(svg_paths)} SVG files"
            )
            
        parsed_paths = []
        for i, svg_path in enumerate(svg_paths):
            # Update progress occasionally for long SVG parsing operations
            if task_id and i % max(1, total_frames // 5) == 0:
                svg_percent = int((i / total_frames) * 100)
                task_queue.update_progress(
                    task_id=task_id,
                    current_step="Parsing SVG files",
                    details=f"Parsing SVG file {i+1}/{len(svg_paths)} ({svg_percent}%)"
                )
                
            paths = parse_svg_to_paths(svg_path)
            parsed_paths.append(paths)
        
        # Step 4: Create Lottie animation
        current_step += 1
        if task_id:
            task_queue.update_progress(
                task_id=task_id,
                current_step="Generating Lottie animation",
                completed_steps=current_step,
                percent=80,
                details=f"Creating Lottie animation with {len(parsed_paths)} frames at {fps} fps"
            )
            
        lottie_json = create_lottie_animation(parsed_paths, fps, width, height)
        
        # Save Lottie JSON to file
        lottie_filename = f"output_{int(time.time())}.json"
        lottie_path = os.path.join(temp_dir, lottie_filename)
        lottie_path = save_lottie_json(lottie_json, lottie_path)
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
                thumbnail_path = generate_thumbnail_from_frame(first_frame, temp_dir)
                
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

@app.get("/", tags=["General"])
async def root():
    """
    Root endpoint - API health check
    
    Returns a simple message indicating the API is running.
    """
    return {"message": "Video to Lottie Conversion API", "status": "ok"}

@app.get("/test", response_class=HTMLResponse, tags=["UI"], include_in_schema=True)
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
    test_html_path = Path("tests/test_upload.html")
    if test_html_path.exists():
        return test_html_path.read_text()
    else:
        return "<html><body><h1>Test page not found</h1></body></html>"

@app.post("/upload", tags=["Conversion"], summary="Upload and convert video to Lottie")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Video file to convert (.mp4, .mov, .avi, .webm)"),
    fps: int = Query(settings.DEFAULT_FPS, ge=1, le=30, description="Frames per second for the Lottie animation"),
    width: int = Query(settings.DEFAULT_WIDTH, ge=100, le=2000, description="Width of the output Lottie animation"),
    height: int = Query(settings.DEFAULT_HEIGHT, ge=100, le=2000, description="Height of the output Lottie animation")
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
            "status_endpoint": f"/tasks/{task_id}"
        }
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/{task_id}", tags=["Tasks"], summary="Get task status")
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

@app.get("/health")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
