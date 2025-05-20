# High-Complexity Functions Refactoring Design

**Date**: 2025-05-20
**Time**: 23:25

## Overview

This document outlines the specific refactoring approach for the 6 high-complexity functions identified in our baseline metrics. Each function will be refactored using SOLID principles, parameter objects, and appropriate design patterns to reduce complexity and improve maintainability.

## 1. `trace_png_to_svg` (Complexity: 29)

### Current Issues
- High cyclomatic complexity (29)
- Multiple responsibilities (image loading, processing, contour detection, SVG generation)
- Difficult to test and maintain

### Refactoring Approach

```mermaid
classDiagram
    class IImageTracer {
        <<interface>>
        +trace_image(input_path: str, output_path: str, params: ImageTracingParams): str
    }
    
    class ImageTracingParams {
        +threshold: int
        +simplify: bool
        +simplify_tolerance: float
        +min_contour_area: float
        +to_dict(): Dict
    }
    
    class ImageTracingParamBuilder {
        +with_threshold(threshold: int): ImageTracingParamBuilder
        +with_simplification(simplify: bool, tolerance: float): ImageTracingParamBuilder
        +with_min_contour_area(area: float): ImageTracingParamBuilder
        +build(): ImageTracingParams
    }
    
    class BaseImageTracer {
        <<abstract>>
        #load_image(path: str): Image
        #prepare_image(image: Image, params: ImageTracingParams): Image
        #save_output(data: str, path: str): str
    }
    
    class OpenCVImageTracer {
        -contour_detector: IContourDetector
        -svg_generator: ISVGGenerator
        +trace_image(input_path: str, output_path: str, params: ImageTracingParams): str
        -detect_contours(image: Image, params: ImageTracingParams): List[Contour]
    }
    
    class IContourDetector {
        <<interface>>
        +detect_contours(image: Image, threshold: int, min_area: float): List[Contour]
        +simplify_contours(contours: List[Contour], tolerance: float): List[Contour]
    }
    
    class OpenCVContourDetector {
        +detect_contours(image: Image, threshold: int, min_area: float): List[Contour]
        +simplify_contours(contours: List[Contour], tolerance: float): List[Contour]
    }
    
    class ISVGGenerator {
        <<interface>>
        +contours_to_svg(contours: List[Contour], width: int, height: int): str
    }
    
    class SimpleSVGGenerator {
        +contours_to_svg(contours: List[Contour], width: int, height: int): str
        -contour_to_path(contour: Contour): str
    }
    
    IImageTracer <|.. BaseImageTracer
    BaseImageTracer <|-- OpenCVImageTracer
    OpenCVImageTracer --> IContourDetector
    OpenCVImageTracer --> ISVGGenerator
    IContourDetector <|.. OpenCVContourDetector
    ISVGGenerator <|.. SimpleSVGGenerator
```

### Benefits
- **Single Responsibility**: Each class has a single, focused responsibility
- **Open/Closed**: New image tracers or contour detectors can be added without modifying existing code
- **Dependency Inversion**: High-level modules depend on abstractions
- **Reduced Complexity**: Each method has a clear, focused purpose

## 2. `extract_frames` (Complexity: 25)

### Current Issues
- High cyclomatic complexity (25)
- Multiple responsibilities (video loading, frame extraction, image processing, file saving)
- Many optional parameters with complex interactions

### Refactoring Approach

```mermaid
classDiagram
    class IFrameExtractor {
        <<interface>>
        +extract_frames(params: FrameExtractionParams): List[str]
    }
    
    class FrameExtractionParams {
        +input_path: str
        +output_dir: str
        +frame_rate: float
        +max_frames: Optional[int]
        +filename_prefix: str
        +output_format: str
        +resize: Optional[Tuple[int, int]]
        +to_dict(): Dict
    }
    
    class FrameExtractionParamBuilder {
        +with_input_path(path: str): FrameExtractionParamBuilder
        +with_output_dir(dir: str): FrameExtractionParamBuilder
        +with_frame_rate(rate: float): FrameExtractionParamBuilder
        +with_max_frames(max: int): FrameExtractionParamBuilder
        +with_filename_prefix(prefix: str): FrameExtractionParamBuilder
        +with_output_format(format: str): FrameExtractionParamBuilder
        +with_resize(width: int, height: int): FrameExtractionParamBuilder
        +build(): FrameExtractionParams
    }
    
    class BaseFrameExtractor {
        <<abstract>>
        #validate_input(path: str): bool
        #ensure_output_dir(dir: str): bool
        #generate_filename(index: int, params: FrameExtractionParams): str
    }
    
    class OpenCVFrameExtractor {
        -frame_processor: IFrameProcessor
        +extract_frames(params: FrameExtractionParams): List[str]
        -calculate_frame_interval(video_fps: float, target_fps: float): int
        -save_frame(frame: Image, path: str, params: FrameExtractionParams): str
    }
    
    class IFrameProcessor {
        <<interface>>
        +process_frame(frame: Image, params: FrameExtractionParams): Image
    }
    
    class BasicFrameProcessor {
        +process_frame(frame: Image, params: FrameExtractionParams): Image
        -resize_frame(frame: Image, dimensions: Tuple[int, int]): Image
    }
    
    IFrameExtractor <|.. BaseFrameExtractor
    BaseFrameExtractor <|-- OpenCVFrameExtractor
    OpenCVFrameExtractor --> IFrameProcessor
    IFrameProcessor <|.. BasicFrameProcessor
```

### Benefits
- **Parameter Object**: Complex parameters consolidated into a structured object
- **Strategy Pattern**: Frame processing strategy can be swapped out
- **Single Responsibility**: Each class has a clear, focused purpose
- **Testability**: Each component can be tested in isolation

## 3. `convert_video` (Complexity: 24)

### Current Issues
- High cyclomatic complexity (24)
- Too many parameters (13)
- Multiple responsibilities (input validation, ffmpeg command building, progress tracking)
- Complex conditional logic for different formats and options

### Refactoring Approach

```mermaid
classDiagram
    class IVideoConverter {
        <<interface>>
        +convert(params: VideoConversionParams): ConversionResult
    }
    
    class VideoConversionParams {
        +input_path: str
        +output_dir: str
        +output_format: VideoFormat
        +quality: VideoQuality
        +resolution: Optional[VideoResolution]
        +framerate: Optional[int]
        +start_time: Optional[float]
        +end_time: Optional[float]
        +audio_codec: Optional[str]
        +video_codec: Optional[str]
        +bitrate: Optional[str]
        +audio_bitrate: Optional[str]
        +extra_ffmpeg_params: Optional[List[str]]
        +progress_callback: Optional[Callable[[int], None]]
        +to_dict(): Dict
    }
    
    class ConversionResult {
        +success: bool
        +output_path: str
        +error: Optional[str]
        +metadata: Dict[str, Any]
    }
    
    class BaseVideoConverter {
        <<abstract>>
        #validate_input(path: str): bool
        #ensure_output_dir(dir: str): bool
        #generate_output_path(params: VideoConversionParams): str
    }
    
    class FFmpegConverter {
        -command_builder: IFFmpegCommandBuilder
        -progress_parser: IProgressParser
        +convert(params: VideoConversionParams): ConversionResult
        -execute_command(command: List[str], callback: Optional[Callable]): Tuple[bool, str]
    }
    
    class IFFmpegCommandBuilder {
        <<interface>>
        +build_command(params: VideoConversionParams, output_path: str): List[str]
    }
    
    class FormatSpecificCommandBuilder {
        -format_handlers: Dict[VideoFormat, IFormatHandler]
        +build_command(params: VideoConversionParams, output_path: str): List[str]
        -get_handler(format: VideoFormat): IFormatHandler
        -build_base_command(params: VideoConversionParams): List[str]
    }
    
    class IFormatHandler {
        <<interface>>
        +get_format_options(params: VideoConversionParams): List[str]
    }
    
    class MP4FormatHandler {
        +get_format_options(params: VideoConversionParams): List[str]
    }
    
    class WebMFormatHandler {
        +get_format_options(params: VideoConversionParams): List[str]
    }
    
    class GIFFormatHandler {
        +get_format_options(params: VideoConversionParams): List[str]
    }
    
    class IProgressParser {
        <<interface>>
        +parse_progress(line: str): int
        +register_callback(callback: Callable[[int], None]): None
    }
    
    class FFmpegProgressParser {
        -callback: Optional[Callable[[int], None]]
        +parse_progress(line: str): int
        +register_callback(callback: Callable[[int], None]): None
        -extract_time(line: str): float
        -calculate_percentage(current_time: float, total_time: float): int
    }
    
    IVideoConverter <|.. BaseVideoConverter
    BaseVideoConverter <|-- FFmpegConverter
    FFmpegConverter --> IFFmpegCommandBuilder
    FFmpegConverter --> IProgressParser
    IFFmpegCommandBuilder <|.. FormatSpecificCommandBuilder
    FormatSpecificCommandBuilder --> IFormatHandler
    IFormatHandler <|.. MP4FormatHandler
    IFormatHandler <|.. WebMFormatHandler
    IFormatHandler <|.. GIFFormatHandler
    IProgressParser <|.. FFmpegProgressParser
```

### Benefits
- **Strategy Pattern**: Different format handlers for different output formats
- **Parameter Object**: 13 parameters consolidated into a single object
- **Single Responsibility**: Command building, execution, and progress parsing separated
- **Open/Closed**: New formats can be added by implementing IFormatHandler

## 4. `process_video_task` (Complexity: 21)

### Current Issues
- High cyclomatic complexity (21)
- Multiple responsibilities (task management, video processing, error handling)
- Complex conditional logic for different output formats
- Difficult to test due to many dependencies

### Refactoring Approach

```mermaid
classDiagram
    class ITaskProcessor {
        <<interface>>
        +process(task_id: str): TaskResult
        +can_process(task_type: str): bool
    }
    
    class TaskResult {
        +success: bool
        +output_url: Optional[str]
        +error: Optional[str]
        +metadata: Dict[str, Any]
    }
    
    class BaseTaskProcessor {
        <<abstract>>
        #task_queue: ITaskQueue
        #get_task(task_id: str): TaskParams
        #update_task_status(task_id: str, status: str): None
        #update_task_progress(task_id: str, progress: int): None
        #update_task_result(task_id: str, result: Dict[str, Any]): None
        #handle_error(task_id: str, error: str): TaskResult
    }
    
    class VideoTaskProcessor {
        -downloader: IDownloader
        -converter_factory: IConverterFactory
        -uploader: IUploader
        -temp_dir_manager: ITempDirManager
        +process(task_id: str): TaskResult
        +can_process(task_type: str): bool
        -process_lottie_conversion(task: TaskParams): TaskResult
        -process_video_conversion(task: TaskParams): TaskResult
        -track_progress(task_id: str): Callable[[int], None]
    }
    
    class IDownloader {
        <<interface>>
        +download_file(url: str, destination: str): str
    }
    
    class IConverterFactory {
        <<interface>>
        +get_converter(format: str): IConverter
    }
    
    class IUploader {
        <<interface>>
        +upload_file(file_path: str, content_type: str): Dict[str, str]
    }
    
    class ITempDirManager {
        <<interface>>
        +create_temp_dir(): str
        +cleanup_temp_files(dir: str): None
    }
    
    ITaskProcessor <|.. BaseTaskProcessor
    BaseTaskProcessor <|-- VideoTaskProcessor
    VideoTaskProcessor --> IDownloader
    VideoTaskProcessor --> IConverterFactory
    VideoTaskProcessor --> IUploader
    VideoTaskProcessor --> ITempDirManager
```

### Benefits
- **Factory Pattern**: Converter factory creates the appropriate converter
- **Template Method**: Base task processor defines the workflow
- **Strategy Pattern**: Different processors for different task types
- **Dependency Injection**: All dependencies are injected and can be mocked for testing

## 5. `convert_video_format_task` (Complexity: 15)

### Current Issues
- High cyclomatic complexity (15)
- Many parameters (13)
- Similar issues to `process_video_task`
- Duplicated code for task management

### Refactoring Approach

```mermaid
classDiagram
    class ITaskProcessor {
        <<interface>>
        +process(task_id: str): TaskResult
        +can_process(task_type: str): bool
    }
    
    class BaseTaskProcessor {
        <<abstract>>
        #task_queue: ITaskQueue
        #get_task(task_id: str): TaskParams
        #update_task_status(task_id: str, status: str): None
        #update_task_progress(task_id: str, progress: int): None
        #update_task_result(task_id: str, result: Dict[str, Any]): None
        #handle_error(task_id: str, error: str): TaskResult
    }
    
    class VideoFormatTaskProcessor {
        -converter: IVideoConverter
        -uploader: IUploader
        -temp_dir_manager: ITempDirManager
        +process(task_id: str): TaskResult
        +can_process(task_type: str): bool
        -build_conversion_params(task: TaskParams): VideoConversionParams
        -track_progress(task_id: str): Callable[[int], None]
    }
    
    ITaskProcessor <|.. BaseTaskProcessor
    BaseTaskProcessor <|-- VideoFormatTaskProcessor
    VideoFormatTaskProcessor --> IVideoConverter
    VideoFormatTaskProcessor --> IUploader
    VideoFormatTaskProcessor --> ITempDirManager
```

### Benefits
- **Inheritance**: Reuses base task processor logic
- **Parameter Object**: Uses VideoConversionParams to simplify parameter handling
- **Single Responsibility**: Focused on video format conversion tasks only
- **DRY Principle**: Eliminates duplication with other task processors

## 6. `parse_svg_to_paths` (Complexity: 11)

### Current Issues
- Moderate cyclomatic complexity (11)
- Multiple responsibilities (file loading, XML parsing, path extraction, transformation)
- Complex handling of different SVG elements

### Refactoring Approach

```mermaid
classDiagram
    class ISVGParser {
        <<interface>>
        +parse_svg_to_paths(svg_path: str): List[Dict]
    }
    
    class BaseSVGParser {
        <<abstract>>
        #load_svg_file(path: str): Document
        #validate_svg(document: Document): bool
    }
    
    class SVGParser {
        -element_handlers: Dict[str, IElementHandler]
        +parse_svg_to_paths(svg_path: str): List[Dict]
        -process_element(element: Element): Optional[Dict]
        -apply_transform(path_data: Dict, transform: str): Dict
    }
    
    class IElementHandler {
        <<interface>>
        +can_handle(element: Element): bool
        +handle_element(element: Element): Dict
    }
    
    class PathElementHandler {
        +can_handle(element: Element): bool
        +handle_element(element: Element): Dict
        -parse_style_attributes(element: Element): Dict
    }
    
    class RectElementHandler {
        +can_handle(element: Element): bool
        +handle_element(element: Element): Dict
        -rect_to_path(x: float, y: float, width: float, height: float): str
    }
    
    class CircleElementHandler {
        +can_handle(element: Element): bool
        +handle_element(element: Element): Dict
        -circle_to_path(cx: float, cy: float, r: float): str
    }
    
    class EllipseElementHandler {
        +can_handle(element: Element): bool
        +handle_element(element: Element): Dict
        -ellipse_to_path(cx: float, cy: float, rx: float, ry: float): str
    }
    
    class PolygonElementHandler {
        +can_handle(element: Element): bool
        +handle_element(element: Element): Dict
        -polygon_to_path(points: str): str
    }
    
    ISVGParser <|.. BaseSVGParser
    BaseSVGParser <|-- SVGParser
    SVGParser --> IElementHandler
    IElementHandler <|.. PathElementHandler
    IElementHandler <|.. RectElementHandler
    IElementHandler <|.. CircleElementHandler
    IElementHandler <|.. EllipseElementHandler
    IElementHandler <|.. PolygonElementHandler
```

### Benefits
- **Chain of Responsibility**: Element handlers process different SVG elements
- **Single Responsibility**: Each handler focuses on one element type
- **Open/Closed**: New element types can be supported by adding new handlers
- **Testability**: Each handler can be tested independently

## Implementation Strategy

The implementation of these refactorings will follow a phased approach:

1. **Phase 1**: Create interfaces and base classes
2. **Phase 2**: Implement concrete classes with minimal functionality
3. **Phase 3**: Migrate existing code to use the new architecture
4. **Phase 4**: Add comprehensive tests for each component

Each function will be refactored one at a time, starting with the most complex (`trace_png_to_svg`) and working down to the least complex. This approach allows us to establish patterns and reuse them across multiple functions.

## Expected Outcomes

- **Reduced Complexity**: Each method will have a cyclomatic complexity < 10
- **Improved Readability**: Clear, focused classes with single responsibilities
- **Enhanced Testability**: Components can be tested in isolation
- **Better Maintainability**: Changes to one component won't affect others
- **Code Reduction**: Overall code size will be reduced by eliminating duplication

By applying these refactoring patterns consistently across all high-complexity functions, we'll achieve a more maintainable, extensible, and robust codebase.
