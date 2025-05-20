# Project Brief: Video Converter

## Overview

Video Converter is a production-ready backend service that converts video files into Lottie JSON animations and between different video formats with optimization options. The service features background processing, real-time progress tracking, and Cloudflare R2 storage integration.

## Core Functionality

1. **Video to Lottie Conversion**: Convert videos (.mp4, .mov, .avi, .webm, .mkv, .flv, .wmv, .m4v) to Lottie JSON animations
2. **Video Format Conversion**: Convert videos between different formats with optimization options
3. **Background Processing**: Asynchronous processing with real-time progress tracking
4. **Cloud Storage**: Cloudflare R2 integration for storing and serving converted files

## Key Features

- Multiple quality presets (low, medium, high, veryhigh)
- Configurable dimensions, bitrate, and encoding settings
- Advanced encoding options (CRF, preset, audio settings)
- Configurable frame rate (fps) and dimensions
- Automatic vector tracing using OpenCV
- Automatic thumbnail generation for previews
- Public access to uploaded files with branded URLs
- Interactive test UIs with progress visualization
- Comprehensive API documentation with Swagger UI

## Project Goals

1. Provide a robust, production-ready video conversion service
2. Support high-quality Lottie animations from video sources
3. Offer flexible video format conversion with optimization options
4. Ensure reliable background processing with progress tracking
5. Integrate seamlessly with cloud storage for file serving

## Target Users

- Developers integrating video conversion functionality into their applications
- Content creators needing to convert videos to Lottie animations
- Users requiring video format conversion with specific optimization settings

## Success Criteria

- Reliable video to Lottie conversion with high-quality results
- Efficient video format conversion with multiple optimization options
- Robust background processing system with accurate progress tracking
- Seamless integration with Cloudflare R2 for file storage and serving
- Comprehensive API documentation and interactive testing interfaces
