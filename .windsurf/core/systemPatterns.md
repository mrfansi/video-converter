# System Patterns: Video Converter

## Architecture Overview

The Video Converter service follows a modular architecture with clear separation of concerns. The system is built around FastAPI as the web framework, with background processing for asynchronous operations and Cloudflare R2 integration for storage.

## Design Patterns

### 1. SOLID Principles Implementation

**Pattern**: SOLID Design Principles
**Implementation**: `app/lottie/` package
**Description**: The Lottie generation functionality implements SOLID principles with clear interfaces and dependency injection.

**Key Components**:
- **Single Responsibility Principle**: Each class has a single responsibility (e.g., `SVGElementsParser` for parsing, `LottieGenerator` for animation generation)
- **Open/Closed Principle**: The system is open for extension through interfaces (`IImageProcessor`, `ISVGParser`, `ILottieGenerator`)
- **Liskov Substitution Principle**: Implementations can be swapped without affecting the system behavior
- **Interface Segregation**: Clean interfaces with focused methods
- **Dependency Inversion**: High-level modules depend on abstractions, not concrete implementations

### 2. Strategy Pattern

**Pattern**: Strategy
**Implementation**: 
- `app/infrastructure/video_processor.py`
- `app/infrastructure/frame_extractor.py`
- `app/infrastructure/video_converter.py`
- `app/lottie/image_processor_refactored.py`
**Description**: The Strategy pattern is used to encapsulate different algorithms for video processing, frame extraction, video conversion, and image tracing, making them interchangeable and reducing cyclomatic complexity.

**Key Components**:
- **Interfaces**: Clear interfaces for each strategy (`IVideoProcessingStrategy`, `IFrameExtractionStrategy`, `IVideoConversionStrategy`, `IImageTracingStrategy`)
- **Concrete Strategies**: Multiple implementations for different quality levels and performance characteristics (Standard, HighQuality, Fast)
- **Context Classes**: Classes that use the strategies (`VideoProcessor`, `FrameExtractor`, `VideoConverter`, `RefactoredImageProcessor`)
- **Parameter Objects**: Strongly-typed parameter objects with validation for each strategy (`VideoProcessingParams`, `FrameExtractionParams`, `VideoConversionParams`, `ImageTracingParams`)
- **Builder Pattern**: Fluent interfaces for constructing parameter objects

```python
# Strategy pattern usage example
params = VideoProcessingParamBuilder()\
    .with_file_path(file_path)\
    .with_temp_dir(temp_dir)\
    .with_fps(fps)\
    .with_dimensions(width, height)\
    .with_strategy(VideoProcessingStrategy.STANDARD)\
    .build()

processor = VideoProcessor()
result = processor.process_video(params)
```

### 3. Facade Pattern

**Pattern**: Facade
**Implementation**: `app/lottie/facade.py`
**Description**: The `LottieGeneratorFacade` provides a simplified interface to the complex subsystem of Lottie generation components.

**Key Components**:
- Unified API for client code
- Composition of specialized components
- Dependency injection support
- Simplified method signatures

```python
# Facade usage example
facade = LottieGeneratorFacade()
result = facade.convert_video_frames_to_lottie(png_frames, output_dir, output_path)
```

### 4. Asynchronous Task Processing

**Pattern**: Background Task Queue
**Implementation**: `app/task_queue.py`
**Description**: The system uses a background task queue to handle video processing asynchronously, allowing the API to respond immediately while processing continues in the background.

**Flow**:
```
Client Request → API Endpoint → Task Queue → Background Processing → Cloud Storage → Status Updates
```

**Key Components**:
- Task data structure with status tracking
- Worker thread pool (configurable number of workers)
- Task persistence with JSON storage
- Progress tracking with percentage and step information
- Handler registration for different task types
- Error handling and recovery

### 5. Storage Abstraction

**Pattern**: Repository Pattern
**Implementation**: `app/uploader.py`
**Description**: The storage layer is abstracted through a repository pattern, allowing for potential future storage provider changes without affecting the core application logic.

**Key Components**:
- Cloudflare R2 integration via boto3's S3-compatible API
- Upload functionality with public URL generation
- Configurable path prefixes and bucket names
- Error handling and retry logic
- Health check functionality

### 6. Configuration Management

**Pattern**: Environment-based Configuration with Pydantic
**Implementation**: `app/config.py`
**Description**: The application uses Pydantic for type-safe environment variable configuration, making it easily deployable across different environments.

**Key Components**:
- Environment variable loading with defaults
- Configuration validation through Pydantic models
- Typed configuration objects
- Separation of concerns for different configuration categories

### 7. Video Processing Pipeline

**Pattern**: Pipeline Pattern
**Implementation**: `app/lottie_generator.py`, `app/utils.py`, `app/video_converter.py`
**Description**: Video processing follows a pipeline pattern with discrete steps that can be monitored and reported on individually.

**Lottie Conversion Pipeline**:
```
Video Input → Frame Extraction → Frame Preparation → Contour Detection → SVG Generation → SVG Parsing → Lottie JSON Assembly → Output
```

**Video Format Conversion Pipeline**:
```
Video Input → Format Validation → Parameter Application → Encoding Process → Output Generation → Thumbnail Creation
```

### 8. Progress Tracking

**Pattern**: Observer Pattern
**Implementation**: `app/task_queue.py`
**Description**: The system implements an observer pattern to track and report progress of background tasks.

**Key Components**:
- Progress update method with multiple tracking dimensions
- Status reporting endpoint with real-time updates
- Percentage calculation based on steps or explicit values
- Detailed progress information including current step and details
- Task persistence for progress recovery after restarts

## API Design

**Pattern**: RESTful API with FastAPI
**Implementation**: `app/main.py`
**Description**: The API follows RESTful principles with clear endpoint definitions, input validation, and comprehensive documentation.

**Key Endpoints**:
- `/video-converter/upload`: POST endpoint for video to Lottie conversion
- `/video-converter/convert`: POST endpoint for video format conversion
- `/video-converter/formats`: GET endpoint for supported format information
- `/video-converter/tasks/{task_id}`: GET endpoint for task status checking
- `/video-converter/test`: GET endpoint for interactive testing UI
- `/video-converter/test-convert`: GET endpoint for testing video format conversion
- `/video-converter/health`: GET endpoint for service health checking

**API Features**:
- Input validation with Pydantic models
- Automatic OpenAPI documentation
- CORS middleware for cross-origin requests
- Background task handling
- Comprehensive error responses

## Error Handling

**Pattern**: Centralized Error Handling
**Implementation**: Throughout the codebase
**Description**: The system implements centralized error handling with appropriate HTTP status codes and error messages.

**Key Components**:
- Exception handling for processing errors
- Appropriate HTTP status codes
- Detailed error messages
- Logging with different severity levels
- Task status updates on errors

## Deployment Architecture

**Pattern**: Containerization
**Implementation**: `Dockerfile`
**Description**: The application is containerized for consistent deployment across environments.

**Deployment Options**:
- Docker container deployment
- EasyPanel deployment with Nixpacks
- Traditional Python deployment with dependencies

## Thumbnail Generation

**Pattern**: Side Effect Processing
**Implementation**: `app/thumbnail_generator.py`
**Description**: The system automatically generates thumbnails for videos and Lottie animations as a side effect of the main processing pipeline.

**Key Components**:
- Frame extraction for video thumbnails
- Image processing for optimal thumbnail generation
- Aspect ratio preservation
- Cloud storage integration for thumbnail serving
- URL generation for thumbnail access
