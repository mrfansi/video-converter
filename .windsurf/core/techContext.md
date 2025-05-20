# Technology Context: Video Converter

## Technology Stack

### Backend Framework
- **FastAPI**: Modern, high-performance web framework for building APIs with Python
- **Uvicorn**: ASGI server for running FastAPI applications
- **Pydantic**: Data validation and settings management using Python type annotations

### Video Processing
- **ffmpeg**: Powerful multimedia framework for video processing
- **ffmpeg-python**: Python bindings for ffmpeg
- **OpenCV**: Computer vision library used for image processing and contour detection
- **Pillow**: Python Imaging Library for image manipulation

### Vector Processing
- **svgelements**: Library for SVG path parsing and manipulation
- **svglib**: Library for working with SVG files
- **lottie**: Library for working with Lottie animations

### Storage
- **boto3**: AWS SDK for Python, used for Cloudflare R2 integration via S3-compatible API

### Utilities
- **numpy**: Numerical computing library for Python
- **scikit-learn**: Machine learning library used for data processing
- **matplotlib**: Visualization library for Python
- **python-dotenv**: Library for loading environment variables from .env files
- **python-multipart**: Library for handling multipart form data
- **requests**: HTTP library for Python

## Development Environment

### Language
- **Python 3.9+**: Main programming language

### System Dependencies
- **ffmpeg**: Required for video frame extraction and processing

### Environment Configuration
- **.env file**: Contains configuration for Cloudflare R2 and other settings
- **Environment variables**: Used for configuration in production environments

## Deployment Options

### Docker
- **Dockerfile**: Configuration for containerized deployment
- **Docker commands**: For building and running the container

### EasyPanel with Nixpacks
- **nixpacks.toml**: Configuration for EasyPanel deployment
- **System dependencies**: Specified in the Nixpacks configuration

### Traditional Deployment
- **requirements.txt**: Python dependencies for traditional deployment
- **uvicorn**: Server for running the FastAPI application

## External Services

### Cloudflare R2
- **S3-compatible API**: For storing and serving files
- **Custom domain support**: For branded URLs
- **Access control**: Public access to uploaded files

## Development Tools

### API Documentation
- **Swagger UI**: Interactive API documentation
- **ReDoc**: Alternative API documentation interface

### Testing
- **Interactive test UI**: For testing the video conversion functionality
- **Test client**: For API testing

## System Requirements

### Server
- **Python 3.9+**: Required for running the application
- **ffmpeg**: Required for video processing
- **Sufficient storage**: For temporary file processing
- **Sufficient memory**: For handling video processing operations

### Client
- **Modern web browser**: For accessing the test UI and API documentation
- **HTTP client**: For making API requests
