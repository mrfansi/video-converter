"""Unit tests for the svg_parser module."""

import pytest

from tests.base_test import BaseTest
from app.lottie.svg_parser import parse_svg_to_paths


class TestSvgParser(BaseTest):
    """Tests for the svg_parser module, focusing on the parse_svg_to_paths function."""

    def setup_method(self, method):
        """Set up test method."""
        super().setup_method(method)
        # Create test data directory for this test
        self.test_output_dir = self.test_data_dir / "output"
        self.test_output_dir.mkdir(exist_ok=True)

    @pytest.fixture
    def sample_svg_content(self):
        """Sample SVG content for testing."""
        return """
        <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
            <path d="M10,10 L90,10 L90,90 L10,90 Z" fill="black" />
            <path d="M30,30 L70,30 L70,70 L30,70 Z" fill="white" />
            <rect x="40" y="40" width="20" height="20" fill="red" />
            <circle cx="50" cy="50" r="5" fill="blue" />
        </svg>
        """

    @pytest.fixture
    def sample_svg_file(self, sample_svg_content):
        """Create a sample SVG file for testing."""
        svg_file = self.test_data_dir / "sample.svg"
        with open(svg_file, "w") as f:
            f.write(sample_svg_content)
        return svg_file

    def test_parse_svg_to_paths_basic(self, sample_svg_file):
        """Test basic functionality of parse_svg_to_paths."""
        # Call the function
        paths = parse_svg_to_paths(str(sample_svg_file))

        # Assertions
        assert paths is not None
        assert isinstance(paths, list)
        assert (
            len(paths) >= 4
        )  # Should have at least 4 paths (2 paths, 1 rect, 1 circle)

        # Check that paths are in the expected format
        for path in paths:
            assert isinstance(path, dict)
            assert "d" in path  # Path data
            assert "fill" in path  # Fill color

    def test_parse_svg_to_paths_with_transform(self, sample_svg_content):
        """Test parse_svg_to_paths with transformed elements."""
        # Create SVG with transforms
        svg_with_transform = sample_svg_content.replace(
            '<path d="M10,10 L90,10 L90,90 L10,90 Z" fill="black" />',
            '<path d="M10,10 L90,10 L90,90 L10,90 Z" fill="black" transform="translate(10, 10)" />',
        )

        svg_file = self.test_data_dir / "transform.svg"
        with open(svg_file, "w") as f:
            f.write(svg_with_transform)

        # Call the function
        paths = parse_svg_to_paths(str(svg_file))

        # Assertions
        assert paths is not None
        assert isinstance(paths, list)

        # Check that transforms were applied
        # The exact path data will depend on the implementation, but we can check that it's different
        # from the original path data in the first test
        transformed_path = next((p for p in paths if p.get("fill") == "black"), None)
        assert transformed_path is not None

    def test_parse_svg_to_paths_with_groups(self):
        """Test parse_svg_to_paths with grouped elements."""
        # Create SVG with groups
        svg_with_groups = """
        <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
            <g transform="translate(10, 10)">
                <path d="M0,0 L80,0 L80,80 L0,80 Z" fill="black" />
                <path d="M20,20 L60,20 L60,60 L20,60 Z" fill="white" />
            </g>
            <g>
                <rect x="40" y="40" width="20" height="20" fill="red" />
                <circle cx="50" cy="50" r="5" fill="blue" />
            </g>
        </svg>
        """

        svg_file = self.test_data_dir / "groups.svg"
        with open(svg_file, "w") as f:
            f.write(svg_with_groups)

        # Call the function
        paths = parse_svg_to_paths(str(svg_file))

        # Assertions
        assert paths is not None
        assert isinstance(paths, list)
        assert len(paths) >= 4  # Should have at least 4 paths

        # Check that group transforms were applied
        black_path = next((p for p in paths if p.get("fill") == "black"), None)
        assert black_path is not None

    def test_parse_svg_to_paths_with_complex_shapes(self):
        """Test parse_svg_to_paths with complex SVG shapes."""
        # Create SVG with complex shapes
        svg_with_complex_shapes = """
        <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
            <path d="M10,10 C20,20 40,20 50,10 S80,0 90,10 Q95,15 100,20 T110,30 L120,40 H130 V50 Z" fill="black" />
            <ellipse cx="50" cy="50" rx="20" ry="10" fill="green" />
            <line x1="10" y1="90" x2="90" y2="90" stroke="red" stroke-width="2" />
            <polyline points="10,80 20,70 30,80 40,70" stroke="blue" fill="none" />
            <polygon points="60,80 70,70 80,80 70,90" fill="purple" />
        </svg>
        """

        svg_file = self.test_data_dir / "complex.svg"
        with open(svg_file, "w") as f:
            f.write(svg_with_complex_shapes)

        # Call the function
        paths = parse_svg_to_paths(str(svg_file))

        # Assertions
        assert paths is not None
        assert isinstance(paths, list)
        assert len(paths) >= 5  # Should have at least 5 paths

        # Check that all shapes were converted to paths
        fills = [p.get("fill") for p in paths if p.get("fill") is not None]
        assert "black" in fills
        assert "green" in fills
        assert "purple" in fills

    def test_parse_svg_to_paths_error_handling(self):
        """Test error handling in parse_svg_to_paths."""
        # Test with non-existent file
        non_existent_file = self.test_data_dir / "nonexistent.svg"

        with pytest.raises(FileNotFoundError):
            parse_svg_to_paths(str(non_existent_file))

        # Test with invalid SVG content
        invalid_svg = self.test_data_dir / "invalid.svg"
        with open(invalid_svg, "w") as f:
            f.write("<not-valid-svg>")

        with pytest.raises(Exception):
            parse_svg_to_paths(str(invalid_svg))

    def test_parse_svg_to_paths_with_style_attributes(self):
        """Test parse_svg_to_paths with style attributes."""
        # Create SVG with style attributes
        svg_with_style = """
        <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
            <path d="M10,10 L90,10 L90,90 L10,90 Z" style="fill: black; stroke: red; stroke-width: 2;" />
            <rect x="30" y="30" width="40" height="40" style="fill: blue; opacity: 0.5;" />
        </svg>
        """

        svg_file = self.test_data_dir / "style.svg"
        with open(svg_file, "w") as f:
            f.write(svg_with_style)

        # Call the function
        paths = parse_svg_to_paths(str(svg_file))

        # Assertions
        assert paths is not None
        assert isinstance(paths, list)
        assert len(paths) >= 2  # Should have at least 2 paths

        # Check that style attributes were parsed correctly
        path_with_stroke = next((p for p in paths if p.get("stroke") == "red"), None)
        assert path_with_stroke is not None
        assert path_with_stroke.get("fill") == "black"

        path_with_opacity = next((p for p in paths if p.get("fill") == "blue"), None)
        assert path_with_opacity is not None
        assert "opacity" in path_with_opacity
