import unittest
from unittest.mock import patch, MagicMock, PropertyMock

from app.models.svg_parsing_params import SVGParsingParams, SVGParsingStrategy
from app.infrastructure.svg_parsing.svg_parser import SVGParserProcessor


class TestSVGParserProcessor(unittest.TestCase):
    """Test cases for the SVGParserProcessor class"""

    def setUp(self):
        self.parser = SVGParserProcessor()
        self.test_svg_path = "test_svg.svg"

    def create_mock_svg(self):
        """Create a mock SVG with test elements"""
        # Create a mock SVG object
        mock_svg = MagicMock()

        # Create mock elements
        mock_path_element = MagicMock()
        mock_path_element.__class__.__name__ = "Path"

        # Create mock segments
        mock_move_segment = MagicMock()
        mock_move_segment.__class__.__name__ = "Move"
        mock_move_segment.end.x = 10
        mock_move_segment.end.y = 20

        mock_line_segment = MagicMock()
        mock_line_segment.__class__.__name__ = "Line"
        mock_line_segment.end.x = 30
        mock_line_segment.end.y = 40

        mock_path_element.__iter__.return_value = [mock_move_segment, mock_line_segment]
        mock_path_element.closed = False

        # Add the mock path element to the mock SVG elements
        mock_svg.elements.return_value = [mock_path_element]

        return mock_svg

    @patch("app.infrastructure.svg_parsing.svg_parser.SVG")
    def test_select_strategy(self, mock_svg_class):
        """Test strategy selection based on parameters"""
        # Test with no parameters
        strategy = self.parser.select_strategy(None)
        self.assertEqual(strategy, self.parser.standard_strategy)

        # Test with standard strategy
        params = SVGParsingParams(
            svg_path=self.test_svg_path, strategy=SVGParsingStrategy.STANDARD
        )
        strategy = self.parser.select_strategy(params)
        self.assertEqual(strategy, self.parser.standard_strategy)

        # Test with optimized strategy
        params = SVGParsingParams(
            svg_path=self.test_svg_path, strategy=SVGParsingStrategy.OPTIMIZED
        )
        strategy = self.parser.select_strategy(params)
        self.assertEqual(strategy, self.parser.optimized_strategy)

        # Test with simplified strategy
        params = SVGParsingParams(
            svg_path=self.test_svg_path, strategy=SVGParsingStrategy.SIMPLIFIED
        )
        strategy = self.parser.select_strategy(params)
        self.assertEqual(strategy, self.parser.simplified_strategy)

        # Test with enhanced strategy
        params = SVGParsingParams(
            svg_path=self.test_svg_path, strategy=SVGParsingStrategy.ENHANCED
        )
        strategy = self.parser.select_strategy(params)
        self.assertEqual(strategy, self.parser.enhanced_strategy)

        # Test with fallback strategy
        params = SVGParsingParams(
            svg_path=self.test_svg_path, strategy=SVGParsingStrategy.FALLBACK
        )
        strategy = self.parser.select_strategy(params)
        self.assertEqual(strategy, self.parser.fallback_strategy)

        # Test with unknown strategy (using a string instead of enum)
        # This should default to standard strategy
        with patch.object(
            SVGParsingParams,
            "strategy",
            create=True,
            new_callable=PropertyMock,
            return_value="unknown",
        ):
            params = SVGParsingParams(
                svg_path=self.test_svg_path, strategy=SVGParsingStrategy.STANDARD
            )
            strategy = self.parser.select_strategy(params)
            self.assertEqual(strategy, self.parser.standard_strategy)

    @patch("svgelements.SVG")
    def test_parse_svg_to_paths_standard(self, mock_svg_class):
        """Test parsing SVG to paths with standard strategy"""
        # Set up mock SVG and elements
        mock_svg = MagicMock()
        mock_element = MagicMock()
        mock_svg.__iter__.return_value = [mock_element]
        mock_svg_class.parse.return_value = mock_svg

        # Create parameters with standard strategy
        params = SVGParsingParams(svg_path=self.test_svg_path, strategy="standard")

        # Mock the strategy to return a valid path
        mock_path = {"ty": "sh", "ks": {"k": {"v": [[0, 0], [10, 10]]}}}
        with patch.object(
            self.parser.standard_strategy, "parse_path_element", return_value=mock_path
        ):
            # Call the method
            result = self.parser.parse_svg_to_paths(self.test_svg_path, params)

            # Verify the result
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0], mock_path)
            mock_svg_class.parse.assert_called_once_with(self.test_svg_path)

    @patch("svgelements.SVG")
    def test_parse_svg_to_paths_no_paths_found(self, mock_svg_class):
        """Test when no paths are found in the SVG"""
        # Set up the mock SVG class to return an empty list
        mock_svg = MagicMock()
        mock_svg.__iter__.return_value = []  # No elements
        mock_svg_class.parse.return_value = mock_svg

        # Create parameters with standard strategy
        params = SVGParsingParams(svg_path=self.test_svg_path, strategy="standard")

        # Call the method
        result = self.parser.parse_svg_to_paths(self.test_svg_path, params)

        # Verify the result - should return an empty list
        self.assertEqual(result, [])

    @patch("svgelements.SVG")
    def test_parse_svg_to_paths_error(self, mock_svg_class):
        """Test when SVG parsing raises an error"""
        # Set up the mock SVG class to raise an exception
        mock_svg_class.parse.side_effect = Exception("Test exception")

        # Create parameters with standard strategy
        params = SVGParsingParams(svg_path=self.test_svg_path, strategy="standard")

        # Call the method
        result = self.parser.parse_svg_to_paths(self.test_svg_path, params)

        # Verify the result - should return an empty list
        self.assertEqual(result, [])

    @patch("svgelements.SVG")
    def test_parse_svg_to_paths_fallback_after_error(self, mock_svg_class):
        """Test fallback strategy after error"""
        # Set up mock SVG and elements
        mock_svg = MagicMock()
        mock_element = MagicMock()
        mock_svg.__iter__.return_value = [mock_element]
        mock_svg_class.parse.return_value = mock_svg

        # Create parameters with standard strategy
        params = SVGParsingParams(svg_path=self.test_svg_path, strategy="standard")

        # Create a mock path for the fallback strategy
        mock_path = {"ty": "sh", "ks": {"k": {"v": [[0, 0], [10, 10]]}}}

        # Make the standard strategy fail but fallback succeed
        with patch.object(
            self.parser.standard_strategy,
            "parse_path_element",
            side_effect=Exception("Test exception"),
        ):
            with patch.object(
                self.parser.fallback_strategy,
                "parse_path_element",
                return_value=mock_path,
            ):

                # Call the method
                result = self.parser.parse_svg_to_paths(self.test_svg_path, params)

                # Verify the result - should have one path from fallback
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0], mock_path)

    @patch("svgelements.SVG")
    def test_parse_svg_to_paths_fallback_also_fails(self, mock_svg_class):
        """Test when fallback strategy also fails"""
        # Set up mock SVG and elements
        mock_svg = MagicMock()
        mock_element = MagicMock()
        mock_svg.__iter__.return_value = [mock_element]
        mock_svg_class.parse.return_value = mock_svg

        # Create parameters with standard strategy
        params = SVGParsingParams(svg_path=self.test_svg_path, strategy="standard")

        # Make both strategies fail
        with patch.object(
            self.parser.standard_strategy,
            "parse_path_element",
            side_effect=Exception("First exception"),
        ):
            with patch.object(
                self.parser.fallback_strategy,
                "parse_path_element",
                side_effect=Exception("Second exception"),
            ):

                # Call the method
                result = self.parser.parse_svg_to_paths(self.test_svg_path, params)

                # Verify the result - should return an empty list
                self.assertEqual(result, [])

    @patch(
        "app.infrastructure.svg_parsing.svg_parser.SVGParserProcessor.parse_svg_to_paths"
    )
    def test_parse_svg_paths_to_lottie_format(self, mock_parse):
        """Test parsing multiple SVG files to Lottie format"""
        # Set up the mock to return test paths
        test_path = {"ty": "sh", "ks": {"k": {"v": [[10, 20], [30, 40]]}}}
        mock_parse.return_value = [test_path]

        # Call the method with multiple SVG paths
        svg_paths = ["path1.svg", "path2.svg", "path3.svg"]
        result = self.parser.parse_svg_paths_to_lottie_format(svg_paths)

        # Verify the result
        self.assertEqual(len(result), 3)  # One frame per SVG path
        self.assertEqual(len(result[0]), 1)  # One path per frame
        self.assertEqual(result[0][0], test_path)
        self.assertEqual(result[1][0], test_path)
        self.assertEqual(result[2][0], test_path)

        # Verify that parse_svg_to_paths was called for each SVG path
        self.assertEqual(mock_parse.call_count, 3)


if __name__ == "__main__":
    unittest.main()
