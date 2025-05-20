"""Concrete implementations of color extraction strategies.

This module provides concrete implementations of the color extraction
interfaces defined in app.domain.interfaces.image_tracing.
"""

from typing import List, Tuple, Optional
import numpy as np
import cv2
import logging

try:
    from sklearn.cluster import KMeans

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from app.domain.models.image_tracing import BaseColorExtractionStrategy

logger = logging.getLogger(__name__)


class DominantColorStrategy(BaseColorExtractionStrategy):
    """Color extraction strategy using dominant color clustering.

    This strategy uses K-means clustering to find dominant colors in the image,
    which works well for images with distinct color regions.
    """

    def __init__(self, max_colors: int = 8):
        """Initialize the dominant color strategy.

        Args:
            max_colors (int, optional): Maximum number of colors to extract. Defaults to 8.
        """
        self.max_colors = max_colors

    def _extract_colors(
        self, image: np.ndarray, contours: List[np.ndarray]
    ) -> List[Tuple[int, int, int]]:
        """Extract dominant colors from the image.

        Args:
            image (np.ndarray): Image to extract colors from (OpenCV format)
            contours (List[np.ndarray]): Contours to extract colors for

        Returns:
            List[Tuple[int, int, int]]: List of RGB colors for each contour
        """
        if not SKLEARN_AVAILABLE:
            logger.warning(
                "sklearn not available, using centroid color extraction instead"
            )
            centroid_strategy = CentroidColorStrategy()
            return centroid_strategy._extract_colors(image, contours)

        # Convert to RGB (from BGR)
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Reshape image for color clustering
        pixels = img_rgb.reshape(-1, 3)

        # Determine optimal number of clusters based on image complexity
        pixel_std = np.std(pixels, axis=0).mean()
        complexity_factor = min(
            max(int(pixel_std / 10), 3), self.max_colors
        )  # Between 3-max_colors
        logger.info(
            f"Image complexity factor: {complexity_factor} (std: {pixel_std:.2f})"
        )

        # Use K-means to find dominant colors with adaptive cluster count
        try:
            # Use complexity-based cluster count with a minimum of 3 colors
            cluster_count = min(complexity_factor, len(set(map(tuple, pixels))))
            kmeans = KMeans(n_clusters=cluster_count, n_init=1)
            kmeans.fit(pixels)
            dominant_colors = kmeans.cluster_centers_.astype(int)

            # Sort colors by frequency (most common first)
            labels = kmeans.labels_
            counts = np.bincount(labels)
            sorted_indices = np.argsort(-counts)  # Descending order
            dominant_colors = dominant_colors[sorted_indices]

            logger.info(f"Extracted {len(dominant_colors)} dominant colors")

            # Convert to RGB tuples
            rgb_colors = [(int(r), int(g), int(b)) for r, g, b in dominant_colors]

            # Assign colors to contours based on position and size
            contour_colors = self._assign_colors_to_contours(
                image, contours, rgb_colors
            )

            return contour_colors
        except Exception as e:
            logger.warning(
                f"Color clustering failed, using centroid color extraction instead: {str(e)}"
            )
            centroid_strategy = CentroidColorStrategy()
            return centroid_strategy._extract_colors(image, contours)

    def _assign_colors_to_contours(
        self,
        image: np.ndarray,
        contours: List[np.ndarray],
        dominant_colors: List[Tuple[int, int, int]],
    ) -> List[Tuple[int, int, int]]:
        """Assign colors to contours based on position and size.

        Args:
            image (np.ndarray): Original image (OpenCV format)
            contours (List[np.ndarray]): Contours to assign colors to
            dominant_colors (List[Tuple[int, int, int]]): List of dominant colors

        Returns:
            List[Tuple[int, int, int]]: List of RGB colors for each contour
        """
        height, width = image.shape[:2]
        contour_colors = []

        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)

            # For larger contours, sample the color from the image at the contour's center
            if area > 100:  # For significant contours, sample actual color
                # Calculate centroid of contour
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])

                    # Ensure coordinates are within image bounds
                    cx = max(0, min(cx, width - 1))
                    cy = max(0, min(cy, height - 1))

                    # Sample color at centroid (BGR format)
                    b, g, r = image[cy, cx]
                    contour_colors.append((r, g, b))
                else:
                    # Fallback to dominant colors if centroid calculation fails
                    color_idx = i % len(dominant_colors)
                    contour_colors.append(dominant_colors[color_idx])
            else:
                # Use dominant colors for smaller contours
                color_idx = i % len(dominant_colors)
                contour_colors.append(dominant_colors[color_idx])

        return contour_colors


class CentroidColorStrategy(BaseColorExtractionStrategy):
    """Color extraction strategy using contour centroids.

    This strategy extracts colors from the image at the centroid of each contour,
    which works well for contours that represent distinct objects.
    """

    def _extract_colors(
        self, image: np.ndarray, contours: List[np.ndarray]
    ) -> List[Tuple[int, int, int]]:
        """Extract colors at contour centroids.

        Args:
            image (np.ndarray): Image to extract colors from (OpenCV format)
            contours (List[np.ndarray]): Contours to extract colors for

        Returns:
            List[Tuple[int, int, int]]: List of RGB colors for each contour
        """
        height, width = image.shape[:2]
        contour_colors = []

        # Default colors in case centroid calculation fails
        default_colors = [
            (0, 0, 0),  # Black
            (255, 0, 0),  # Red
            (0, 255, 0),  # Green
            (0, 0, 255),  # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (128, 128, 128),  # Gray
        ]

        for i, contour in enumerate(contours):
            # Calculate centroid of contour
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                # Ensure coordinates are within image bounds
                cx = max(0, min(cx, width - 1))
                cy = max(0, min(cy, height - 1))

                # Sample color at centroid (BGR format)
                b, g, r = image[cy, cx]
                contour_colors.append((r, g, b))
            else:
                # Fallback to default colors if centroid calculation fails
                color_idx = i % len(default_colors)
                contour_colors.append(default_colors[color_idx])

        return contour_colors


class AverageColorStrategy(BaseColorExtractionStrategy):
    """Color extraction strategy using average color within contour masks.

    This strategy calculates the average color within each contour's mask,
    which provides a more accurate representation of the object's color.
    """

    def _extract_colors(
        self, image: np.ndarray, contours: List[np.ndarray]
    ) -> List[Tuple[int, int, int]]:
        """Extract average colors within contour masks.

        Args:
            image (np.ndarray): Image to extract colors from (OpenCV format)
            contours (List[np.ndarray]): Contours to extract colors for

        Returns:
            List[Tuple[int, int, int]]: List of RGB colors for each contour
        """
        height, width = image.shape[:2]
        contour_colors = []

        # Convert to RGB (from BGR)
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        for contour in contours:
            # Create mask for this contour
            mask = np.zeros((height, width), dtype=np.uint8)
            cv2.drawContours(mask, [contour], 0, 255, -1)

            # Apply mask to image
            masked_img = cv2.bitwise_and(img_rgb, img_rgb, mask=mask)

            # Calculate average color within mask
            mask_pixels = np.where(mask == 255)
            if len(mask_pixels[0]) > 0:  # If mask has any pixels
                avg_color = np.mean(masked_img[mask_pixels], axis=0).astype(int)
                r, g, b = avg_color
                contour_colors.append((r, g, b))
            else:
                # Fallback for empty masks
                contour_colors.append((0, 0, 0))  # Black

        return contour_colors


class HybridColorStrategy(BaseColorExtractionStrategy):
    """Hybrid color extraction strategy combining multiple approaches.

    This strategy combines multiple color extraction approaches to get the best results,
    particularly useful for complex images with varying characteristics.
    """

    def __init__(
        self,
        dominant_strategy: Optional[DominantColorStrategy] = None,
        centroid_strategy: Optional[CentroidColorStrategy] = None,
        average_strategy: Optional[AverageColorStrategy] = None,
    ):
        """Initialize the hybrid color strategy.

        Args:
            dominant_strategy (Optional[DominantColorStrategy], optional): Dominant color strategy. Defaults to None.
            centroid_strategy (Optional[CentroidColorStrategy], optional): Centroid color strategy. Defaults to None.
            average_strategy (Optional[AverageColorStrategy], optional): Average color strategy. Defaults to None.
        """
        self.dominant_strategy = dominant_strategy or DominantColorStrategy()
        self.centroid_strategy = centroid_strategy or CentroidColorStrategy()
        self.average_strategy = average_strategy or AverageColorStrategy()

    def _extract_colors(
        self, image: np.ndarray, contours: List[np.ndarray]
    ) -> List[Tuple[int, int, int]]:
        """Extract colors using a hybrid approach.

        Args:
            image (np.ndarray): Image to extract colors from (OpenCV format)
            contours (List[np.ndarray]): Contours to extract colors for

        Returns:
            List[Tuple[int, int, int]]: List of RGB colors for each contour
        """
        # Get colors from each strategy
        try:
            dominant_colors = self.dominant_strategy._extract_colors(image, contours)
        except Exception as e:
            logger.warning(f"Dominant color strategy failed: {str(e)}")
            dominant_colors = [(0, 0, 0)] * len(contours)  # Black fallback

        try:
            centroid_colors = self.centroid_strategy._extract_colors(image, contours)
        except Exception as e:
            logger.warning(f"Centroid color strategy failed: {str(e)}")
            centroid_colors = [(0, 0, 0)] * len(contours)  # Black fallback

        try:
            average_colors = self.average_strategy._extract_colors(image, contours)
        except Exception as e:
            logger.warning(f"Average color strategy failed: {str(e)}")
            average_colors = [(0, 0, 0)] * len(contours)  # Black fallback

        # Combine colors based on contour characteristics
        combined_colors = []

        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)

            if (
                i < len(dominant_colors)
                and i < len(centroid_colors)
                and i < len(average_colors)
            ):
                if area < 50:  # Small contours
                    # Use dominant colors for small contours
                    combined_colors.append(dominant_colors[i])
                elif area < 500:  # Medium contours
                    # Use centroid colors for medium contours
                    combined_colors.append(centroid_colors[i])
                else:  # Large contours
                    # Use average colors for large contours
                    combined_colors.append(average_colors[i])
            else:
                # Fallback if index out of range
                combined_colors.append((0, 0, 0))  # Black

        return combined_colors
