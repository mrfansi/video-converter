import os
import sys
import json
import logging
import tempfile
import time
import matplotlib.pyplot as plt

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils import extract_frames, prepare_frame_for_tracing
from app.lottie import LottieGeneratorFacade

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_video_to_lottie(
    video_path, output_dir=None, fps=10, width=640, height=480, max_frames=50
):
    """
    Convert a video to a Lottie JSON animation with color preservation

    Args:
        video_path (str): Path to the video file
        output_dir (str): Directory to save the output files (if None, uses a temp directory)
        fps (int): Frames per second for the animation
        width (int): Width of the animation
        height (int): Height of the animation
        max_frames (int): Maximum number of frames to process

    Returns:
        dict: Results containing paths to the generated files and analysis data
    """
    start_time = time.time()
    results = {
        "video_path": video_path,
        "fps": fps,
        "width": width,
        "height": height,
        "max_frames": max_frames,
        "timings": {},
        "stats": {},
        "paths": {},
    }

    # Create output directory if not provided
    if output_dir is None:
        temp_dir = tempfile.mkdtemp()
        output_dir = temp_dir

    try:
        # Create directories for intermediate files
        frames_dir = os.path.join(output_dir, "frames")
        svg_dir = os.path.join(output_dir, "svg")
        os.makedirs(frames_dir, exist_ok=True)
        os.makedirs(svg_dir, exist_ok=True)

        # Step 1: Extract frames from video
        logger.info(f"Extracting frames from {video_path} at {fps} fps")
        extract_start = time.time()
        frame_paths = extract_frames(
            video_path, frames_dir, fps=fps, width=width, height=height
        )
        extract_end = time.time()
        results["timings"]["extract_frames"] = extract_end - extract_start
        results["stats"]["total_frames"] = len(frame_paths)
        logger.info(
            f"Extracted {len(frame_paths)} frames in {results['timings']['extract_frames']:.2f} seconds"
        )

        # Limit frames if needed
        if max_frames and len(frame_paths) > max_frames:
            logger.info(f"Limiting to {max_frames} frames")
            frame_paths = frame_paths[:max_frames]
            results["stats"]["processed_frames"] = max_frames
        else:
            results["stats"]["processed_frames"] = len(frame_paths)

        # Step 2: Process frames and generate SVGs
        logger.info(f"Processing {len(frame_paths)} frames to generate SVGs")
        svg_paths = []
        prepare_times = []
        trace_times = []
        valid_path_counts = []

        for i, frame_path in enumerate(frame_paths):
            # Prepare frame for tracing (color-preserving)
            prepare_start = time.time()
            prepared_frame = prepare_frame_for_tracing(frame_path)
            prepare_end = time.time()
            prepare_times.append(prepare_end - prepare_start)

            # Trace PNG to SVG with color preservation using the facade
            trace_start = time.time()
            lottie_facade = LottieGeneratorFacade()
            svg_path = lottie_facade.trace_png_to_svg(prepared_frame, svg_dir)
            trace_end = time.time()
            trace_times.append(trace_end - trace_start)
            svg_paths.append(svg_path)

            # Extract stats from log output (hacky but works for testing)
            with open(svg_path, "r") as f:
                svg_content = f.read()
                # Count the number of path elements
                path_count = svg_content.count("<path")
                valid_path_counts.append(path_count)

            # Log progress
            if (i + 1) % 10 == 0 or i == len(frame_paths) - 1:
                logger.info(f"Processed {i + 1}/{len(frame_paths)} frames")

        results["timings"]["prepare_frames_avg"] = (
            sum(prepare_times) / len(prepare_times) if prepare_times else 0
        )
        results["timings"]["trace_svg_avg"] = (
            sum(trace_times) / len(trace_times) if trace_times else 0
        )
        results["stats"]["valid_paths_avg"] = (
            sum(valid_path_counts) / len(valid_path_counts) if valid_path_counts else 0
        )

        # Step 3: Create Lottie animation from SVGs
        logger.info(f"Creating Lottie animation from {len(svg_paths)} SVGs")
        lottie_start = time.time()

        # Use the facade to create Lottie animation from SVGs
        lottie_facade = LottieGeneratorFacade()

        # First, parse SVG paths to get the frame data for analysis
        frame_paths = lottie_facade.svg_parser.parse_svg_paths_to_lottie_format(
            svg_paths
        )

        # Create temporary file for Lottie JSON
        temp_lottie_path = os.path.join(output_dir, "temp_animation.json")

        # Create Lottie animation directly from SVG files
        lottie_path = lottie_facade.create_lottie_from_svgs(
            svg_paths=svg_paths,
            output_path=temp_lottie_path,
            fps=fps,
            width=width,
            height=height,
            max_frames=max_frames,
            optimize=True,
            compress=False,  # Don't compress yet for analysis
        )

        # Load the generated JSON for analysis
        with open(lottie_path, "r") as f:
            lottie_json = json.load(f)
        lottie_end = time.time()
        results["timings"]["create_lottie"] = lottie_end - lottie_start

        # Save Lottie JSON
        lottie_path = os.path.join(output_dir, "animation.json")
        with open(lottie_path, "w") as f:
            # Use a custom JSON encoder to handle non-serializable objects
            class CustomJSONEncoder(json.JSONEncoder):
                def default(self, obj):
                    # Convert any non-serializable objects to their string representation
                    try:
                        return json.JSONEncoder.default(self, obj)
                    except TypeError:
                        return str(obj)

            json.dump(lottie_json, f, cls=CustomJSONEncoder)

        # Calculate total processing time
        end_time = time.time()
        results["timings"]["total"] = end_time - start_time

        # Save paths
        results["paths"]["lottie_json"] = lottie_path
        results["paths"]["frames_dir"] = frames_dir
        results["paths"]["svg_dir"] = svg_dir

        # Analyze Lottie JSON
        results["stats"]["lottie_size_kb"] = os.path.getsize(lottie_path) / 1024
        results["stats"]["lottie_layers"] = len(lottie_json.get("layers", []))

        logger.info(
            f"Conversion completed in {results['timings']['total']:.2f} seconds"
        )
        logger.info(
            f"Lottie JSON saved to {lottie_path} ({results['stats']['lottie_size_kb']:.2f} KB)"
        )

        return results

    except Exception as e:
        logger.error(f"Error converting video to Lottie: {str(e)}")
        raise


def analyze_results(results):
    """
    Analyze the results of the video to Lottie conversion

    Args:
        results (dict): Results from convert_video_to_lottie
    """
    print("\n===== VIDEO TO LOTTIE CONVERSION ANALYSIS =====")
    print(f"Video: {results['video_path']}")
    print(f"Dimensions: {results['width']}x{results['height']}")
    print(f"FPS: {results['fps']}")
    print(
        f"Frames: {results['stats']['total_frames']} (processed: {results['stats']['processed_frames']})"
    )

    print("\n--- TIMING ANALYSIS ---")
    print(f"Total processing time: {results['timings']['total']:.2f} seconds")
    print(f"Frame extraction: {results['timings']['extract_frames']:.2f} seconds")
    print(
        f"Average frame preparation: {results['timings']['prepare_frames_avg'] * 1000:.2f} ms/frame"
    )
    print(
        f"Average SVG tracing: {results['timings']['trace_svg_avg'] * 1000:.2f} ms/frame"
    )
    print(f"Lottie generation: {results['timings']['create_lottie']:.2f} seconds")

    print("\n--- OUTPUT ANALYSIS ---")
    print(f"Lottie JSON size: {results['stats']['lottie_size_kb']:.2f} KB")
    print(f"Lottie layers: {results['stats']['lottie_layers']}")
    print(f"Average paths per frame: {results['stats']['valid_paths_avg']:.2f}")

    # Calculate processing rate
    fps_processing = results["stats"]["processed_frames"] / results["timings"]["total"]
    print(f"Processing rate: {fps_processing:.2f} frames/second")

    # Calculate compression ratio (assuming 30KB per frame as a rough estimate for raw video)
    estimated_video_size = results["stats"]["processed_frames"] * 30  # KB
    compression_ratio = estimated_video_size / results["stats"]["lottie_size_kb"]
    print(f"Estimated compression ratio: {compression_ratio:.2f}x")

    # Print file locations
    print("\n--- OUTPUT FILES ---")
    print(f"Lottie JSON: {results['paths']['lottie_json']}")
    print(f"Extracted frames: {results['paths']['frames_dir']}")
    print(f"SVG files: {results['paths']['svg_dir']}")


def visualize_results(results):
    """
    Create visualizations of the conversion results

    Args:
        results (dict): Results from convert_video_to_lottie
    """
    # Create a figure with multiple subplots
    fig = plt.figure(figsize=(12, 10))
    fig.suptitle("Video to Lottie Conversion Analysis", fontsize=16)

    # Timing breakdown
    ax1 = fig.add_subplot(221)
    timing_labels = ["Extract", "Prepare", "Trace", "Lottie Gen"]
    timing_values = [
        results["timings"]["extract_frames"],
        results["timings"]["prepare_frames_avg"] * results["stats"]["processed_frames"],
        results["timings"]["trace_svg_avg"] * results["stats"]["processed_frames"],
        results["timings"]["create_lottie"],
    ]
    ax1.bar(timing_labels, timing_values)
    ax1.set_title("Processing Time Breakdown")
    ax1.set_ylabel("Seconds")

    # Processing rate
    ax2 = fig.add_subplot(222)
    fps_processing = results["stats"]["processed_frames"] / results["timings"]["total"]
    ax2.bar(["Processing Rate"], [fps_processing])
    ax2.set_title("Processing Speed")
    ax2.set_ylabel("Frames per Second")

    # File size comparison
    ax3 = fig.add_subplot(223)
    estimated_video_size = (
        results["stats"]["processed_frames"] * 30
    )  # KB (rough estimate)
    size_labels = ["Estimated Video", "Lottie JSON"]
    size_values = [estimated_video_size, results["stats"]["lottie_size_kb"]]
    ax3.bar(size_labels, size_values)
    ax3.set_title("File Size Comparison")
    ax3.set_ylabel("Size (KB)")

    # Compression ratio
    ax4 = fig.add_subplot(224)
    compression_ratio = estimated_video_size / results["stats"]["lottie_size_kb"]
    ax4.bar(["Compression Ratio"], [compression_ratio])
    ax4.set_title("Compression Ratio")
    ax4.set_ylabel("Ratio (higher is better)")

    # Save the figure
    output_dir = os.path.dirname(results["paths"]["lottie_json"])
    plot_path = os.path.join(output_dir, "analysis.png")
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust for the suptitle
    plt.savefig(plot_path)
    print(f"\nAnalysis visualization saved to: {plot_path}")

    return plot_path


if __name__ == "__main__":
    # Get the sample video path
    video_path = os.path.join(os.path.dirname(__file__), "video.webm")

    if not os.path.exists(video_path):
        logger.error(f"Sample video not found at {video_path}")
        sys.exit(1)

    # Create output directory
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)

    # Convert video to Lottie
    try:
        results = convert_video_to_lottie(
            video_path=video_path,
            output_dir=output_dir,
            fps=10,
            width=640,
            height=480,
            max_frames=30,  # Limit to 30 frames for testing
        )

        # Analyze and visualize results
        analyze_results(results)
        visualize_results(results)

        print("\nTest completed successfully!")

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        sys.exit(1)
