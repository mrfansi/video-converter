"""Concrete implementations of contour extraction strategies.

This module provides concrete implementations of the contour extraction
interfaces defined in app.domain.interfaces.image_tracing.
"""

from typing import List, Tuple, Optional
import numpy as np
import cv2
import logging

from app.domain.models.image_tracing import BaseContourExtractionStrategy

logger = logging.getLogger(__name__)


class AdaptiveThresholdStrategy(BaseContourExtractionStrategy):
    """Contour extraction strategy using adaptive thresholding.

    This strategy uses adaptive thresholding to extract contours from images,
    which works well for images with varying brightness levels.
    """

    def __init__(self, block_size: int = 11, c_value: int = 2):
        """Initialize the adaptive threshold strategy.

        Args:
            block_size (int, optional): Block size for adaptive thresholding. Defaults to 11.
            c_value (int, optional): Constant subtracted from mean. Defaults to 2.
        """
        self.block_size = block_size
        self.c_value = c_value

    def _extract_contours(
        self, image: np.ndarray
    ) -> Tuple[List[np.ndarray], np.ndarray]:
        """Extract contours using adaptive thresholding.

        Args:
            image (np.ndarray): Image to extract contours from (OpenCV format)

        Returns:
            Tuple[List[np.ndarray], np.ndarray]: Tuple of (contours, processed_image)
        """
        # Convert to LAB color space for better edge detection
        img_lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

        # Extract the L channel from LAB
        l_channel = img_lab[:, :, 0]

        # Apply bilateral filter to reduce noise while preserving edges
        filtered = cv2.bilateralFilter(l_channel, 9, 75, 75)

        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(
            filtered,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            self.block_size,
            self.c_value,
        )

        # Apply morphological operations to clean up the image
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        # Find contours
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS
        )

        return contours, thresh


class ColorBasedSegmentationStrategy(BaseContourExtractionStrategy):
    """Contour extraction strategy using color-based segmentation.

    This strategy uses color-based segmentation to extract contours from images,
    which works well for images with distinct color regions.
    """

    def _extract_contours(
        self, image: np.ndarray
    ) -> Tuple[List[np.ndarray], np.ndarray]:
        """Extract contours using color-based segmentation.

        Args:
            image (np.ndarray): Image to extract contours from (OpenCV format)

        Returns:
            Tuple[List[np.ndarray], np.ndarray]: Tuple of (contours, processed_image)
        """
        # Convert to LAB color space for better edge detection
        img_lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

        # Extract the L channel from LAB
        l_channel = img_lab[:, :, 0]

        # Apply bilateral filter to reduce noise while preserving edges
        filtered = cv2.bilateralFilter(l_channel, 9, 75, 75)

        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(
            filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )

        # Color-based region segmentation
        # Convert to HSV for better color segmentation
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Extract saturation channel which helps identify colorful areas
        sat_channel = hsv[:, :, 1]

        # Apply Otsu's thresholding to find significant color regions
        _, sat_mask = cv2.threshold(
            sat_channel, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        # Combine with edge detection for better results
        combined_mask = cv2.bitwise_or(thresh, sat_mask)

        # Clean up the combined mask
        kernel = np.ones((3, 3), np.uint8)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(
            combined_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS
        )

        return contours, combined_mask


class CannyEdgeStrategy(BaseContourExtractionStrategy):
    """Contour extraction strategy using Canny edge detection.

    This strategy uses Canny edge detection to extract contours from images,
    which works well for images with clear edges.
    """

    def __init__(self, low_threshold: int = 50, high_threshold: int = 150):
        """Initialize the Canny edge strategy.

        Args:
            low_threshold (int, optional): Low threshold for Canny. Defaults to 50.
            high_threshold (int, optional): High threshold for Canny. Defaults to 150.
        """
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold

    def _extract_contours(
        self, image: np.ndarray
    ) -> Tuple[List[np.ndarray], np.ndarray]:
        """Extract contours using Canny edge detection.

        Args:
            image (np.ndarray): Image to extract contours from (OpenCV format)

        Returns:
            Tuple[List[np.ndarray], np.ndarray]: Tuple of (contours, processed_image)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Apply Canny edge detection
        edges = cv2.Canny(blurred, self.low_threshold, self.high_threshold)

        # Dilate edges to connect nearby edges
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)

        # Find contours
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS
        )

        return contours, dilated


class HybridContourStrategy(BaseContourExtractionStrategy):
    """Hybrid contour extraction strategy combining multiple approaches.

    This strategy combines multiple contour extraction approaches to get the best results,
    particularly useful for complex images with varying characteristics.
    """

    def __init__(
        self,
        adaptive_strategy: Optional[AdaptiveThresholdStrategy] = None,
        color_strategy: Optional[ColorBasedSegmentationStrategy] = None,
        canny_strategy: Optional[CannyEdgeStrategy] = None,
    ):
        """Initialize the hybrid contour strategy.

        Args:
            adaptive_strategy (Optional[AdaptiveThresholdStrategy], optional): Adaptive threshold strategy. Defaults to None.
            color_strategy (Optional[ColorBasedSegmentationStrategy], optional): Color-based segmentation strategy. Defaults to None.
            canny_strategy (Optional[CannyEdgeStrategy], optional): Canny edge strategy. Defaults to None.
        """
        self.adaptive_strategy = adaptive_strategy or AdaptiveThresholdStrategy()
        self.color_strategy = color_strategy or ColorBasedSegmentationStrategy()
        self.canny_strategy = canny_strategy or CannyEdgeStrategy()

    def _extract_contours(
        self, image: np.ndarray
    ) -> Tuple[List[np.ndarray], np.ndarray]:
        """Extract contours using a hybrid approach.

        Args:
            image (np.ndarray): Image to extract contours from (OpenCV format)

        Returns:
            Tuple[List[np.ndarray], np.ndarray]: Tuple of (contours, processed_image)
        """
        # Get contours from each strategy
        adaptive_contours, adaptive_image = self.adaptive_strategy._extract_contours(
            image
        )
        color_contours, color_image = self.color_strategy._extract_contours(image)
        canny_contours, canny_image = self.canny_strategy._extract_contours(image)

        # Combine all contours
        all_contours = adaptive_contours + color_contours + canny_contours

        # Create a combined image for visualization
        combined_image = cv2.bitwise_or(adaptive_image, color_image)
        combined_image = cv2.bitwise_or(combined_image, canny_image)

        # Remove duplicate contours (those with similar position and shape)
        filtered_contours = self._remove_duplicate_contours(all_contours)

        logger.info(
            f"Hybrid strategy found {len(all_contours)} contours, filtered to {len(filtered_contours)}"
        )

        return filtered_contours, combined_image

    def _remove_duplicate_contours(
        self, contours: List[np.ndarray]
    ) -> List[np.ndarray]:
        """Remove duplicate contours based on position and shape similarity.

        Args:
            contours (List[np.ndarray]): List of contours

        Returns:
            List[np.ndarray]: Filtered list of contours
        """
        if not contours:
            return []

        # Sort contours by area (largest first)
        sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)

        filtered_contours = [sorted_contours[0]]

        for contour in sorted_contours[1:]:
            is_duplicate = False

            for existing_contour in filtered_contours:
                # Compare contours using shape matching
                similarity = cv2.matchShapes(
                    contour, existing_contour, cv2.CONTOURS_MATCH_I2, 0.0
                )

                # Check if contours have similar position using bounding boxes
                x1, y1, w1, h1 = cv2.boundingRect(contour)
                x2, y2, w2, h2 = cv2.boundingRect(existing_contour)

                # Calculate overlap ratio
                overlap_x = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
                overlap_y = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
                overlap_area = overlap_x * overlap_y

                contour_area = w1 * h1
                existing_area = w2 * h2

                if contour_area > 0 and existing_area > 0:
                    overlap_ratio = overlap_area / min(contour_area, existing_area)
                else:
                    overlap_ratio = 0

                # If contours are similar in shape and position, consider it a duplicate
                if similarity < 0.3 and overlap_ratio > 0.5:
                    is_duplicate = True
                    break

            if not is_duplicate:
                filtered_contours.append(contour)

        return filtered_contours
