import requests
import os
import sys

def test_health():
    """Test the health endpoint"""
    response = requests.get("http://localhost:8000/health")
    print(f"Health check status code: {response.status_code}")
    print(f"Health check response: {response.json()}")

def test_upload(video_path):
    """Test the upload endpoint with a video file"""
    if not os.path.exists(video_path):
        print(f"Error: File {video_path} does not exist")
        return
    
    # Prepare the multipart form data
    url = "http://localhost:8000/upload"
    params = {
        "fps": 30,
        "width": 800,
        "height": 600
    }
    
    # Open the file and create the multipart form data
    with open(video_path, "rb") as f:
        # The key 'file' must match the parameter name in the FastAPI endpoint
        files = {"file": (os.path.basename(video_path), f, "video/mp4")}
        
        print(f"Sending request to {url} with file {video_path}")
        response = requests.post(url, params=params, files=files)
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    # Test the health endpoint
    print("Testing health endpoint...")
    test_health()
    print("\n" + "-"*50 + "\n")
    
    # Test the upload endpoint if a file path is provided
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        print(f"Testing upload endpoint with file: {video_path}")
        test_upload(video_path)
    else:
        print("Please provide a video file path as an argument to test the upload endpoint")
        print("Example: python test_client.py /path/to/video.mp4")
