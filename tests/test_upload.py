import requests
import os
import sys
import argparse

def upload_video(video_path, fps=10, width=800, height=600):
    """Upload a video file to the video-to-lottie service"""
    # Validate file exists
    if not os.path.exists(video_path):
        print(f"Error: File {video_path} does not exist")
        return False
    
    # Validate file is a video
    allowed_extensions = [".mp4", ".mov", ".avi", ".webm"]
    _, ext = os.path.splitext(video_path)
    if ext.lower() not in allowed_extensions:
        print(f"Error: File must be one of {', '.join(allowed_extensions)}")
        return False
    
    # Prepare the request
    url = "http://localhost:8000/upload"
    params = {
        "fps": fps,
        "width": width,
        "height": height
    }
    
    # Open the file in binary mode
    with open(video_path, "rb") as video_file:
        # Create the files dictionary with the file field
        files = {
            "file": (os.path.basename(video_path), video_file, "video/mp4")
        }
        
        # Print request details for debugging
        print(f"Uploading {video_path} to {url}")
        print(f"Parameters: {params}")
        
        # Make the request
        try:
            response = requests.post(url, params=params, files=files)
            
            # Print the response status and content
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Check if the request was successful
            if response.status_code == 200:
                print("\nUpload successful!")
                return True
            else:
                print("\nUpload failed.")
                return False
        except Exception as e:
            print(f"Error making request: {str(e)}")
            return False

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Upload a video to the video-to-lottie service")
    parser.add_argument("video_path", help="Path to the video file to upload")
    parser.add_argument("--fps", type=int, default=10, help="Frames per second (default: 10)")
    parser.add_argument("--width", type=int, default=800, help="Output width (default: 800)")
    parser.add_argument("--height", type=int, default=600, help="Output height (default: 600)")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Upload the video
    upload_video(args.video_path, args.fps, args.width, args.height)

if __name__ == "__main__":
    main()
