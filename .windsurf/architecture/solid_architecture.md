# SOLID Architecture Design for Video Converter

**Date**: 2025-05-20
**Time**: 23:20

## Overview

This document outlines the new architecture for the Video Converter project following SOLID principles. The architecture is designed to improve maintainability, reduce code size, and enhance extensibility while maintaining the core functionality of the system.

## SOLID Principles Implementation

### Single Responsibility Principle (SRP)

Each class will have only one reason to change, focusing on a single responsibility:

- **Converters**: Responsible only for conversion logic
- **Storage**: Responsible only for file storage
- **Task Management**: Responsible only for task queuing and status tracking
- **API Layer**: Responsible only for handling HTTP requests and responses

### Open/Closed Principle (OCP)

The architecture is designed to be open for extension but closed for modification:

- **Strategy Pattern**: For different conversion algorithms
- **Plugin System**: For adding new output formats without changing core code
- **Event System**: For adding new behaviors without modifying existing code

### Liskov Substitution Principle (LSP)

Subtypes must be substitutable for their base types:

- **Converter Interfaces**: All converters implement the same interface
- **Storage Providers**: All storage providers are interchangeable
- **Task Processors**: All task processors follow the same contract

### Interface Segregation Principle (ISP)

Clients should not depend on interfaces they don't use:

- **Specialized Interfaces**: Smaller, focused interfaces instead of large, general ones
- **Role-Based Interfaces**: Interfaces defined by the role they play in the system

### Dependency Inversion Principle (DIP)

High-level modules should not depend on low-level modules; both should depend on abstractions:

- **Dependency Injection**: All dependencies injected through constructors or methods
- **Service Locator**: For resolving dependencies at runtime
- **Abstract Factories**: For creating families of related objects

## Core Architecture Components

### 1. Domain Layer

```mermaid
classDiagram
    class IConverter {
        <<interface>>
        +convert(params: ConversionParams): ConversionResult
    }
    
    class IStorage {
        <<interface>>
        +upload(file_path: str, content_type: str): StorageResult
        +download(key: str, destination: str): StorageResult
        +delete(key: str): bool
    }
    
    class ITaskProcessor {
        <<interface>>
        +process(task_id: str): TaskResult
    }
    
    class BaseParams {
        <<abstract>>
        +to_dict(): Dict
        +from_dict(data: Dict): BaseParams
    }
    
    class ConversionResult {
        +success: bool
        +output_path: str
        +error: Optional[str]
    }
    
    class StorageResult {
        +success: bool
        +key: str
        +url: str
        +error: Optional[str]
    }
    
    class TaskResult {
        +success: bool
        +output_url: Optional[str]
        +error: Optional[str]
    }
    
    BaseParams <|-- VideoConversionParams
    BaseParams <|-- LottieAnimationParams
    BaseParams <|-- TaskParams
```

### 2. Application Layer

```mermaid
classDiagram
    class VideoConverterService {
        -converters: Dict[str, IConverter]
        -storage: IStorage
        +convert_video(params: VideoConversionParams): ConversionResult
        +convert_to_lottie(params: LottieAnimationParams): ConversionResult
    }
    
    class TaskQueueService {
        -task_processors: Dict[str, ITaskProcessor]
        -storage: IStorage
        +add_task(params: TaskParams): str
        +get_task(task_id: str): TaskParams
        +update_task(params: TaskUpdateParams): bool
        +process_task(task_id: str): TaskResult
    }
    
    class StorageService {
        -storage_provider: IStorage
        +upload_file(file_path: str, content_type: str): StorageResult
        +download_file(url: str, destination: str): StorageResult
    }
    
    VideoConverterService --> IConverter: uses
    VideoConverterService --> IStorage: uses
    TaskQueueService --> ITaskProcessor: uses
    TaskQueueService --> IStorage: uses
    StorageService --> IStorage: uses
```

### 3. Infrastructure Layer

```mermaid
classDiagram
    class FFmpegConverter {
        -ffmpeg_path: str
        +convert(params: VideoConversionParams): ConversionResult
    }
    
    class LottieGenerator {
        -image_processor: ImageProcessor
        -svg_parser: SVGParser
        +generate_from_frames(params: LottieAnimationParams): ConversionResult
    }
    
    class CloudflareR2Storage {
        -client: S3Client
        -bucket: str
        -endpoint: str
        +upload(file_path: str, content_type: str): StorageResult
        +download(key: str, destination: str): StorageResult
        +delete(key: str): bool
    }
    
    class InMemoryTaskQueue {
        -tasks: Dict[str, TaskParams]
        +add_task(params: TaskParams): str
        +get_task(task_id: str): TaskParams
        +update_task(params: TaskUpdateParams): bool
    }
    
    class VideoTaskProcessor {
        -converter: IConverter
        -storage: IStorage
        +process(task_id: str): TaskResult
    }
    
    class LottieTaskProcessor {
        -generator: LottieGenerator
        -storage: IStorage
        +process(task_id: str): TaskResult
    }
    
    IConverter <|.. FFmpegConverter
    IConverter <|.. LottieGenerator
    IStorage <|.. CloudflareR2Storage
    ITaskProcessor <|.. VideoTaskProcessor
    ITaskProcessor <|.. LottieTaskProcessor
```

### 4. API Layer

```mermaid
classDiagram
    class APIRouter {
        +register_routes(app: FastAPI): None
    }
    
    class VideoConverterRouter {
        -converter_service: VideoConverterService
        -task_service: TaskQueueService
        +register_routes(app: FastAPI): None
        +convert_video(request: Request): Response
        +convert_to_lottie(request: Request): Response
    }
    
    class TaskRouter {
        -task_service: TaskQueueService
        +register_routes(app: FastAPI): None
        +add_task(request: Request): Response
        +get_task(task_id: str): Response
        +update_task(task_id: str, request: Request): Response
    }
    
    APIRouter <|-- VideoConverterRouter
    APIRouter <|-- TaskRouter
    VideoConverterRouter --> VideoConverterService: uses
    VideoConverterRouter --> TaskQueueService: uses
    TaskRouter --> TaskQueueService: uses
```

## Detailed Component Design

### 1. Video Conversion Module

```mermaid
classDiagram
    class IVideoConverter {
        <<interface>>
        +convert(params: VideoConversionParams): ConversionResult
    }
    
    class BaseVideoConverter {
        <<abstract>>
        #validate_input(input_path: str): bool
        #create_output_dir(output_dir: str): bool
        #parse_progress(line: str): int
    }
    
    class FFmpegConverter {
        -ffmpeg_path: str
        -codec_map: Dict[str, Dict[str, str]]
        +convert(params: VideoConversionParams): ConversionResult
        -build_ffmpeg_command(params: VideoConversionParams): List[str]
        -handle_progress(line: str, callback: Callable): None
    }
    
    class GIFConverter {
        -ffmpeg_path: str
        +convert(params: VideoConversionParams): ConversionResult
        -optimize_gif(input_path: str, output_path: str): bool
    }
    
    class WebMConverter {
        -ffmpeg_path: str
        +convert(params: VideoConversionParams): ConversionResult
        -set_webm_options(params: VideoConversionParams): List[str]
    }
    
    IVideoConverter <|.. BaseVideoConverter
    BaseVideoConverter <|-- FFmpegConverter
    BaseVideoConverter <|-- GIFConverter
    BaseVideoConverter <|-- WebMConverter
```

### 2. Lottie Generation Module

```mermaid
classDiagram
    class ILottieGenerator {
        <<interface>>
        +generate_from_frames(params: LottieAnimationParams): ConversionResult
        +generate_from_svgs(params: SVGConversionParams): ConversionResult
    }
    
    class ImageProcessor {
        +trace_png_to_svg(input_path: str, output_path: str): str
        -simplify_contours(contours: List, tolerance: float): List
        -contours_to_svg_paths(contours: List): List[str]
    }
    
    class SVGParser {
        +parse_svg_to_paths(svg_path: str): List[Dict]
        -process_path_element(element: Element): Dict
        -process_shape_element(element: Element): Dict
    }
    
    class LottieBuilder {
        +create_animation(width: int, height: int, fps: int): Dict
        +add_layer(animation: Dict, layer_data: Dict): Dict
        +add_shape(layer: Dict, shape_data: Dict): Dict
        +optimize(animation: Dict, level: int): Dict
    }
    
    class LottieGenerator {
        -image_processor: ImageProcessor
        -svg_parser: SVGParser
        -lottie_builder: LottieBuilder
        +generate_from_frames(params: LottieAnimationParams): ConversionResult
        +generate_from_svgs(params: SVGConversionParams): ConversionResult
        -process_frame(frame_path: str, temp_dir: str): str
        -combine_frames(svg_paths: List[str], params: LottieAnimationParams): Dict
    }
    
    ILottieGenerator <|.. LottieGenerator
    LottieGenerator --> ImageProcessor: uses
    LottieGenerator --> SVGParser: uses
    LottieGenerator --> LottieBuilder: uses
```

### 3. Storage Module

```mermaid
classDiagram
    class IStorage {
        <<interface>>
        +upload(file_path: str, content_type: str): StorageResult
        +download(key: str, destination: str): StorageResult
        +delete(key: str): bool
        +get_public_url(key: str): str
    }
    
    class BaseStorage {
        <<abstract>>
        #validate_file(file_path: str): bool
        #ensure_directory(directory: str): bool
    }
    
    class CloudflareR2Storage {
        -client: S3Client
        -bucket: str
        -endpoint: str
        -path_prefix: str
        -custom_domain: Optional[str]
        +upload(file_path: str, content_type: str): StorageResult
        +download(key: str, destination: str): StorageResult
        +delete(key: str): bool
        +get_public_url(key: str): str
        -generate_key(file_path: str): str
    }
    
    class LocalFileStorage {
        -base_directory: str
        -base_url: str
        +upload(file_path: str, content_type: str): StorageResult
        +download(key: str, destination: str): StorageResult
        +delete(key: str): bool
        +get_public_url(key: str): str
    }
    
    IStorage <|.. BaseStorage
    BaseStorage <|-- CloudflareR2Storage
    BaseStorage <|-- LocalFileStorage
```

### 4. Task Queue Module

```mermaid
classDiagram
    class ITaskQueue {
        <<interface>>
        +add_task(params: TaskParams): str
        +get_task(task_id: str): TaskParams
        +update_task(params: TaskUpdateParams): bool
        +list_tasks(status: Optional[str], limit: int, offset: int): List[TaskParams]
    }
    
    class ITaskProcessor {
        <<interface>>
        +process(task_id: str): TaskResult
        +can_process(task_type: str): bool
    }
    
    class BaseTaskQueue {
        <<abstract>>
        #generate_task_id(): str
        #validate_task(params: TaskParams): bool
    }
    
    class InMemoryTaskQueue {
        -tasks: Dict[str, TaskParams]
        +add_task(params: TaskParams): str
        +get_task(task_id: str): TaskParams
        +update_task(params: TaskUpdateParams): bool
        +list_tasks(status: Optional[str], limit: int, offset: int): List[TaskParams]
    }
    
    class SQLiteTaskQueue {
        -db_path: str
        -connection: Connection
        +add_task(params: TaskParams): str
        +get_task(task_id: str): TaskParams
        +update_task(params: TaskUpdateParams): bool
        +list_tasks(status: Optional[str], limit: int, offset: int): List[TaskParams]
        -init_db(): None
    }
    
    class TaskProcessorRegistry {
        -processors: Dict[str, ITaskProcessor]
        +register_processor(processor: ITaskProcessor): None
        +get_processor(task_type: str): ITaskProcessor
        +process_task(task_id: str): TaskResult
    }
    
    class VideoTaskProcessor {
        -converter: IVideoConverter
        -storage: IStorage
        -task_queue: ITaskQueue
        +process(task_id: str): TaskResult
        +can_process(task_type: str): bool
    }
    
    class LottieTaskProcessor {
        -generator: ILottieGenerator
        -storage: IStorage
        -task_queue: ITaskQueue
        +process(task_id: str): TaskResult
        +can_process(task_type: str): bool
    }
    
    ITaskQueue <|.. BaseTaskQueue
    BaseTaskQueue <|-- InMemoryTaskQueue
    BaseTaskQueue <|-- SQLiteTaskQueue
    ITaskProcessor <|.. VideoTaskProcessor
    ITaskProcessor <|.. LottieTaskProcessor
    TaskProcessorRegistry --> ITaskProcessor: uses
```

## Dependency Injection Container

```mermaid
classDiagram
    class ServiceContainer {
        -services: Dict[Type, Any]
        +register(interface: Type, implementation: Any): None
        +resolve(interface: Type): Any
    }
    
    class AppContainer {
        -container: ServiceContainer
        +configure(): None
        +get_service(interface: Type): Any
    }
    
    AppContainer --> ServiceContainer: uses
```

## Application Startup Flow

```mermaid
sequenceDiagram
    participant Main
    participant Container
    participant FastAPI
    participant Routers
    participant Services
    
    Main->>Container: configure()
    Container->>Container: register_services()
    Main->>FastAPI: create_app()
    FastAPI->>Container: get_service(APIRouter)
    Container->>Routers: create_routers()
    Routers->>Container: get_service(Services)
    Container->>Services: create_services()
    Routers->>FastAPI: register_routes()
    Main->>FastAPI: start()
```

## Task Processing Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant TaskQueue
    participant TaskProcessor
    participant Converter
    participant Storage
    
    Client->>API: POST /tasks
    API->>TaskQueue: add_task()
    TaskQueue->>API: task_id
    API->>Client: task_id
    
    Client->>API: GET /tasks/{task_id}
    API->>TaskQueue: get_task(task_id)
    TaskQueue->>API: task
    API->>Client: task
    
    Note over API,Storage: Background Processing
    
    API->>TaskProcessor: process(task_id)
    TaskProcessor->>TaskQueue: get_task(task_id)
    TaskQueue->>TaskProcessor: task
    TaskProcessor->>TaskQueue: update_status("processing")
    TaskProcessor->>Converter: convert(params)
    
    loop Progress Updates
        Converter->>TaskProcessor: progress_callback(percent)
        TaskProcessor->>TaskQueue: update_progress(percent)
    end
    
    Converter->>TaskProcessor: result
    TaskProcessor->>Storage: upload(result.output_path)
    Storage->>TaskProcessor: storage_result
    TaskProcessor->>TaskQueue: update_result(storage_result)
    TaskProcessor->>TaskQueue: update_status("completed")
```

## Benefits of the New Architecture

1. **Improved Maintainability**:
   - Clear separation of concerns
   - Smaller, focused classes and functions
   - Reduced coupling between components

2. **Enhanced Extensibility**:
   - New formats can be added by implementing interfaces
   - New storage providers can be easily integrated
   - New task processors can be registered without modifying existing code

3. **Better Testability**:
   - Dependencies are injected and can be mocked
   - Interfaces define clear contracts
   - Components can be tested in isolation

4. **Reduced Code Size**:
   - Common functionality extracted to base classes
   - Parameter objects reduce function parameter complexity
   - Shared utilities eliminate duplication

## Implementation Strategy

The implementation of this architecture will follow a phased approach:

1. **Phase 1**: Create interfaces and base classes
2. **Phase 2**: Implement core services with dependency injection
3. **Phase 3**: Refactor existing code to use the new architecture
4. **Phase 4**: Add new features and optimizations

Each phase will be accompanied by comprehensive tests to ensure functionality is maintained throughout the refactoring process.
