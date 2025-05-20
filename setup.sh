#!/bin/bash

# Update package lists
apt-get update -y

# Install OpenCV dependencies
apt-get install -y \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    python3-opencv

# Clean up to reduce image size
apt-get clean
rm -rf /var/lib/apt/lists/*

# Install Python dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "Setup completed successfully!"
