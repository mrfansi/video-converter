# Video-to-Lottie Conversion Service

A production-ready backend service that converts video files into Lottie JSON animations and uploads them to Cloudflare R2 storage with background processing and real-time progress tracking.

## Features

- Convert videos (.mp4, .mov, .avi, .webm) to Lottie JSON animations
- Background processing with real-time progress tracking
- Configurable frame rate (fps) and dimensions
- Automatic vector tracing using OpenCV
- Cloudflare R2 integration with custom domain support
- Public access to uploaded files with branded URLs
- Automatic thumbnail generation for previews
- Returns publicly accessible URLs
- Interactive test UI with progress visualization
- Comprehensive API documentation with Swagger UI

## Tech Stack

- **FastAPI**: Backend server framework
- **ffmpeg**: Video frame extraction
- **OpenCV**: Image processing and contour detection for vectorization
- **svgelements**: SVG path parsing for Lottie compatibility
- **boto3**: Cloudflare R2 integration via S3-compatible API

## Prerequisites

- Python 3.9+
- ffmpeg installed on the system
- Cloudflare R2 account and credentials

### Installing Dependencies

#### System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

#### Python Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your Cloudflare R2 credentials:
   ```
   R2_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
   R2_ACCESS_KEY_ID=<your_access_key_id>
   R2_SECRET_ACCESS_KEY=<your_secret_access_key>
   R2_BUCKET_NAME=lottie-animations
   R2_PATH_PREFIX=lottie
   ```

## Running the Service

### Development Mode

```bash
cd video-to-lottie
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
cd video-to-lottie
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Background Processing System

The service uses a background processing system to handle video conversions asynchronously, providing real-time progress tracking. Key features include:

- **Task Queue**: Manages background tasks with unique task IDs
- **Progress Tracking**: Detailed updates for each processing step
- **Status Endpoint**: API endpoint to check task status and progress
- **Error Handling**: Comprehensive error reporting for failed tasks

### How It Works

1. When a video is uploaded, it's assigned a unique task ID
2. The processing happens in the background while the API returns immediately
3. The client can poll the status endpoint to track progress
4. When processing completes, the status endpoint returns URLs to the results

## Testing with the UI

The service includes an interactive test UI that demonstrates the video-to-lottie conversion process with real-time progress tracking:

1. Start the server: `uvicorn app.main:app --reload`
2. Open the test page in your browser: `http://localhost:8000/test`
3. Upload a video file and configure the conversion parameters
4. Watch the real-time progress tracking as the video is processed
5. When complete, view the Lottie animation directly in the browser

## API Usage

### API Documentation

The API provides comprehensive Swagger documentation at the following endpoints:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

These interactive documentation pages allow you to explore and test all available endpoints.

### Upload Endpoint

**Endpoint:** `POST /upload`

**Form Parameters:**
- `file`: Video file (.mp4, .mov, .avi, .webm)

**Query Parameters:**
- `fps`: Frames per second (default: 30)
- `width`: Output width (default: 800)
- `height`: Output height (default: 600)

**Example Request:**
```bash
curl -X POST "http://localhost:8000/upload?fps=30&width=800&height=600" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@video.mp4"
```

**Example Response (Background Processing):**
```json
{
  "task_id": "1716203414",
  "status": "processing",
  "status_endpoint": "/tasks/1716203414"
}
```

### Task Status Endpoint

**Endpoint:** `GET /tasks/{task_id}`

**Example Request:**
```bash
curl -X GET "http://localhost:8000/tasks/1716203414"
```

**Example Response (In Progress):**
```json
{
  "task_id": "1716203414",
  "status": "processing",
  "progress": {
    "current_step": "Converting frames to SVG",
    "percent": 45,
    "details": "Processing frame 27/60"
  }
}
```

**Example Response (Completed):**
```json
{
  "task_id": "1716203414",
  "status": "completed",
  "progress": {
    "current_step": "Completed",
    "percent": 100,
    "details": "Processing complete"
  },
  "result": {
    "url": "https://video.viding.org/lottie/1716203414.json",
    "thumbnail_url": "https://video.viding.org/lottie/1716203414.png"
  }
}
```

### Test UI Endpoint

**Endpoint:** `GET /test`

**Description:** Serves an HTML page with a form for testing the video-to-lottie conversion with real-time progress tracking and Lottie preview.

**Example Access:**
```
http://localhost:8000/test
```

### Health Check

**Endpoint:** `GET /`

**Example Request:**
```bash
curl -X GET "http://localhost:8000/"
```

**Example Response:**
```json
{
  "message": "Video to Lottie Conversion API",
  "status": "ok"
}
```

## Deployment Options

### Docker Support

A Dockerfile is provided for containerized deployment.

#### Building the Docker Image

```bash
docker build -t video-to-lottie .
```

#### Running the Container

```bash
docker run -p 8000:8000 --env-file .env video-to-lottie
```

### EasyPanel Deployment with Nixpacks

The project includes a `nixpacks.toml` configuration file for easy deployment to EasyPanel.

#### Nixpacks Configuration

The `nixpacks.toml` file includes:

- System dependencies (ffmpeg, OpenCV, required libraries)
- Python 3.12 runtime specification
- Python setup commands
- Start command configuration
- Environment variables

#### Deploying to EasyPanel

1. Push your code to a Git repository
2. In EasyPanel, create a new application
3. Select your repository
4. EasyPanel will automatically detect the `nixpacks.toml` file
5. Set your environment variables (R2 credentials, etc.) in the EasyPanel dashboard

## Project Structure

```
video-to-lottie/
├── app/
│   ├── main.py              # FastAPI app with API endpoints
│   ├── utils.py             # Video processing utilities
│   ├── uploader.py          # Cloudflare R2 upload functionality
│   ├── config.py            # Environment-based configuration
│   ├── lottie_generator.py  # Lottie JSON builder
│   └── task_queue.py        # Background task processing system
├── tests/
│   ├── test_upload.html     # Interactive test UI with progress tracking
│   ├── test_client.py       # API client for testing
│   └── debug_upload.py      # Debugging utility for uploads
├── static/                  # Static files for web UI
│   └── test_upload.html     # Copy of test UI for static serving
├── media/                   # Temporary storage for processing
├── .windsurf/               # Memory Bank for project documentation
├── requirements.txt         # Python dependencies
├── .env.example             # Example environment variables
├── Dockerfile               # Docker configuration
└── README.md                # Documentation
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
