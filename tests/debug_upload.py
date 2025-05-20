#!/usr/bin/env python3

import os
import sys
import json
import time
import argparse
import requests
from typing import Dict, Any, Optional
import threading

def poll_task_status(status_endpoint: str) -> None:
    """Poll the task status endpoint until the task is complete"""
    print("\nPolling for task completion...")
    last_step = ""
    last_percent = 0
    
    while True:
        try:
            response = requests.get(status_endpoint)
            response_json = response.json()
            status = response_json["status"]
            updated_time = time.strftime('%H:%M:%S', time.localtime(response_json['updated_at']))
            
            # Extract progress information if available
            progress = response_json.get("progress", {})
            current_step = progress.get("current_step", "")
            percent = progress.get("percent", 0)
            details = progress.get("details", "")
            completed_steps = progress.get("completed_steps", 0)
            total_steps = progress.get("total_steps", 0)
            
            # Only print if there's a change in step or significant progress change
            if current_step != last_step or abs(percent - last_percent) >= 5:
                # Create progress bar
                bar_length = 30
                filled_length = int(bar_length * percent / 100)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                
                # Print status with progress bar
                print(f"[{bar}] {percent}% | {current_step} | {updated_time}")
                if details:
                    print(f"  ↳ {details}")
                    
                # Update last values
                last_step = current_step
                last_percent = percent
            
            if status == "completed":
                print("\n✅ Task completed!")
                if "result" in response_json:
                    result = response_json["result"]
                    print("Lottie URL:", result.get("url"))
                    print("Thumbnail URL:", result.get("thumbnail_url", "No thumbnail generated"))
                break
            elif status == "failed":
                print("\n❌ Task failed.")
                if "error" in response_json:
                    print(f"Error: {response_json['error']}")
                break
            else:
                # For pending or processing status, wait and try again
                time.sleep(2)  # Reduced wait time for more responsive updates
        except Exception as e:
            print(f"\nError polling task status: {str(e)}")
            break

def debug_upload(video_path: str, server_url: str = "http://localhost:8000", fps: int = 10, width: int = 606, height: int = 1080, verbose: bool = False) -> bool:
    """Debug the upload process with detailed logging"""
    # Check if file exists
    if not os.path.exists(video_path):
        print(f"Error: File {video_path} does not exist")
        return False
    
    # Get file extension
    _, ext = os.path.splitext(video_path)
    allowed_extensions = [".mp4", ".mov", ".avi", ".webm"]
    if ext.lower() not in allowed_extensions:
        print(f"Warning: File extension {ext} might not be supported. Allowed: {', '.join(allowed_extensions)}")
    
    # Prepare request
    upload_url = f"{server_url}/upload"
    params = {
        "fps": fps,
        "width": width,
        "height": height
    }
    
    # Determine content type based on extension
    content_types = {
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".avi": "video/x-msvideo",
        ".webm": "video/webm"
    }
    content_type = content_types.get(ext.lower(), "application/octet-stream")
    
    print(f"\n=== DEBUG INFORMATION ===\n")
    print(f"Upload URL: {upload_url}")
    print(f"Parameters: {params}")
    print(f"File path: {video_path}")
    print(f"File size: {os.path.getsize(video_path)} bytes")
    print(f"Content type: {content_type}")
    
    # First check server health
    try:
        health_response = requests.get(f"{server_url}/health")
        print(f"\nServer health check: {health_response.status_code}")
        print(f"Health response: {health_response.json()}")
    except Exception as e:
        print(f"\nError checking server health: {str(e)}")
        print("Make sure the server is running at the specified URL")
        return False
    
    # Prepare the file for upload
    try:
        with open(video_path, "rb") as video_file:
            # Create multipart form data
            files = {
                "file": (os.path.basename(video_path), video_file, content_type)
            }
            
            print(f"\nSending upload request...")
            
            # Make the request with detailed debugging
            response = requests.post(
                upload_url,
                params=params,
                files=files
            )
            
            print(f"\nResponse status code: {response.status_code}")
            print(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
            
            try:
                response_json = response.json()
                print("Response:", response_json)
                
                # Check if this is a task response
                if "task_id" in response_json:
                    task_id = response_json["task_id"]
                    status_endpoint = response_json["status_endpoint"]
                    print(f"\n🔄 Processing started with task ID: {task_id}")
                    print(f"Status endpoint: {status_endpoint}")
                    
                    # Poll for task completion
                    poll_task_status(upload_url.split("/upload")[0] + status_endpoint)
                else:
                    # Direct response with results
                    print("Lottie URL:", response_json.get("url"))
                    print("Thumbnail URL:", response_json.get("thumbnail_url", "No thumbnail generated"))
                    print("\n✅ Upload successful!")
            except:
                print(f"Response body (raw): {response.text[:500]}")
                if len(response.text) > 500:
                    print("... (truncated)")
                return False
            
            return True
    except Exception as e:
        print(f"\nError during upload: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Debug tool for video-to-lottie upload")
    parser.add_argument("video_path", help="Path to the video file to upload")
    parser.add_argument("--url", default="http://localhost:8000", help="Server URL (default: http://localhost:8000)")
    parser.add_argument("--fps", type=int, default=10, help="Frames per second (default: 10)")
    parser.add_argument("--width", type=int, default=800, help="Output width (default: 800)")
    parser.add_argument("--height", type=int, default=600, help="Output height (default: 600)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    debug_upload(
        args.video_path,
        server_url=args.url,
        fps=args.fps,
        width=args.width,
        height=args.height,
        verbose=args.verbose
    )

if __name__ == "__main__":
    main()
