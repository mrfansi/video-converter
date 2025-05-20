import os
import cv2
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_frames_debug(video_path, output_dir, num_frames=10):
    """Extract a few frames from a video file for debugging"""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Open the video file
    logger.info(f"Opening video file: {video_path}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Could not open video file: {video_path}")
        return []

    # Get video properties
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    logger.info(
        f"Video properties: {total_frames} frames, {video_fps} fps, {width}x{height}"
    )

    # Extract frames
    frame_files = []
    frame_interval = max(1, total_frames // num_frames)

    for i in range(num_frames):
        # Set frame position
        frame_pos = i * frame_interval
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)

        # Read the frame
        ret, frame = cap.read()
        if not ret:
            logger.warning(f"Could not read frame at position {frame_pos}")
            continue

        # Check if frame is blank (all black or all white)
        is_blank = False
        mean_value = np.mean(frame)
        std_value = np.std(frame)

        if mean_value < 5 or mean_value > 250 or std_value < 5:
            logger.warning(
                f"Frame {i} appears to be blank: mean={mean_value}, std={std_value}"
            )
            is_blank = True

        # Save the frame
        frame_file = os.path.join(output_dir, f"debug_frame_{i:04d}.png")
        cv2.imwrite(frame_file, frame)
        frame_files.append(frame_file)

        # Add text annotation if blank
        if is_blank:
            # Create a copy with text
            annotated_frame = frame.copy()
            cv2.putText(
                annotated_frame,
                f"BLANK FRAME: mean={mean_value:.1f}, std={std_value:.1f}",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2,
            )
            annotated_file = os.path.join(
                output_dir, f"debug_frame_{i:04d}_annotated.png"
            )
            cv2.imwrite(annotated_file, annotated_frame)

        logger.info(
            f"Extracted frame {i} at position {frame_pos}: {'BLANK' if is_blank else 'OK'}"
        )

    # Release the video capture object
    cap.release()

    logger.info(f"Extracted {len(frame_files)} frames for debugging")
    return frame_files


# Find a video file to test
def find_video_file():
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith((".mp4", ".mov", ".avi", ".webm")):
                return os.path.join(root, file)
    return None


if __name__ == "__main__":
    # Create output directory
    output_dir = "debug_frames"
    os.makedirs(output_dir, exist_ok=True)

    # Find a video file
    video_path = find_video_file()
    if not video_path:
        logger.error("No video file found for testing")
        exit(1)

    logger.info(f"Testing frame extraction with video: {video_path}")

    # Extract frames
    frames = extract_frames_debug(video_path, output_dir)

    logger.info(f"Extracted {len(frames)} frames for debugging")
    logger.info(f"Check the {output_dir} directory for the extracted frames")
