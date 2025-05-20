#!/bin/bash

# Run the application in development mode with auto-reload
echo "Starting Video Converter API in development mode..."
echo "API will be available at: http://localhost:8000/video-converter/"
echo "Documentation: http://localhost:8000/video-converter/docs"
echo "Press Ctrl+C to stop the server"

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
