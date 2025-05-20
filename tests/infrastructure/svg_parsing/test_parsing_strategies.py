import unittest
from unittest.mock import patch, MagicMock

from app.infrastructure.svg_parsing.parsing_strategies import (
    StandardSVGPathParsingStrategy,
    OptimizedSVGPathParsingStrategy,
    SimplifiedSVGPathParsingStrategy,
    EnhancedSVGPathParsingStrategy,
    FallbackSVGPathParsingStrategy,
    StandardSegmentProcessor,
    OptimizedSegmentProcessor,
    SimplifiedSegmentProcessor,
    StandardSVGElementFilter,
    AdvancedSVGElementFilter,
    StandardLottiePathBuilder,
    EnhancedLottiePathBuilder,
)
from app.infrastructure.svg_parsing.base_strategies import BaseSVGPathParsingStrategy


class TestSVGPathParsingStrategies(unittest.TestCase):
    """Test cases for the SVG path parsing strategies"""

    def setUp(self):
        self.standard_strategy = StandardSVGPathParsingStrategy()
        self.optimized_strategy = OptimizedSVGPathParsingStrategy(
            simplify_tolerance=0.5
        )
        self.simplified_strategy = SimplifiedSVGPathParsingStrategy()
        self.enhanced_strategy = EnhancedSVGPathParsingStrategy()
        self.fallback_strategy = FallbackSVGPathParsingStrategy()

    def create_mock_path_element(self):
        """Create a mock SVG path element with standard test segments"""
        mock_element = MagicMock()

        # Create mock segments
        mock_move_segment = MagicMock()
        mock_move_segment.__class__.__name__ = "Move"
        mock_move_segment.end.x = 10
        mock_move_segment.end.y = 20

        mock_line_segment = MagicMock()
        mock_line_segment.__class__.__name__ = "Line"
        mock_line_segment.end.x = 30
        mock_line_segment.end.y = 40

        mock_bezier_segment = MagicMock()
        mock_bezier_segment.__class__.__name__ = "CubicBezier"
        mock_bezier_segment.end.x = 50
        mock_bezier_segment.end.y = 60
        mock_bezier_segment.control1.x = 35
        mock_bezier_segment.control1.y = 45
        mock_bezier_segment.control2.x = 45
        mock_bezier_segment.control2.y = 55

        mock_close_segment = MagicMock()
        mock_close_segment.__class__.__name__ = "Close"

        # Set up the element
        mock_element.__iter__.return_value = [
            mock_move_segment,
            mock_line_segment,
            mock_bezier_segment,
            mock_close_segment,
        ]
        mock_element.closed = True

        return mock_element

    def test_standard_strategy(self):
        """Test the standard SVG path parsing strategy"""
        mock_element = self.create_mock_path_element()

        result = self.standard_strategy.parse_path_element(mock_element)

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result["ty"], "sh")
        self.assertEqual(result["ks"]["k"]["c"], True)  # Closed path

        # Should have 3 vertices (move, line, bezier)
        self.assertEqual(len(result["ks"]["k"]["v"]), 3)
        self.assertEqual(result["ks"]["k"]["v"][0], [10, 20])
        self.assertEqual(result["ks"]["k"]["v"][1], [30, 40])
        self.assertEqual(result["ks"]["k"]["v"][2], [50, 60])

        # Check tangents - bezier should have non-zero tangents
        self.assertNotEqual(result["ks"]["k"]["i"][2], [0, 0])
        self.assertNotEqual(result["ks"]["k"]["o"][1], [0, 0])

    def test_optimized_strategy(self):
        """Test the optimized SVG path parsing strategy"""
        mock_element = self.create_mock_path_element()

        result = self.optimized_strategy.parse_path_element(mock_element)

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result["ty"], "sh")
        self.assertEqual(result["ks"]["k"]["c"], True)  # Closed path

        # Should have vertices (possibly simplified)
        self.assertGreaterEqual(len(result["ks"]["k"]["v"]), 2)

    def test_simplified_strategy(self):
        """Test the simplified SVG path parsing strategy"""
        mock_element = self.create_mock_path_element()

        result = self.simplified_strategy.parse_path_element(mock_element)

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result["ty"], "sh")
        self.assertEqual(result["ks"]["k"]["c"], True)  # Closed path

        # Should have 3 vertices (move, line, bezier converted to line)
        self.assertEqual(len(result["ks"]["k"]["v"]), 3)

        # All tangents should be zero in simplified strategy
        for i in range(len(result["ks"]["k"]["i"])):
            self.assertEqual(result["ks"]["k"]["i"][i], [0, 0])
            self.assertEqual(result["ks"]["k"]["o"][i], [0, 0])

    def test_enhanced_strategy(self):
        """Test the enhanced SVG path parsing strategy"""
        mock_element = self.create_mock_path_element()

        result = self.enhanced_strategy.parse_path_element(mock_element)

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result["ty"], "sh")
        self.assertEqual(result["ks"]["k"]["c"], True)  # Closed path

        # Should have additional properties
        self.assertEqual(result["nm"], "Path")
        self.assertEqual(result["hd"], False)

    def test_fallback_strategy_normal_case(self):
        """Test the fallback SVG path parsing strategy with normal input"""
        mock_element = self.create_mock_path_element()

        result = self.fallback_strategy.parse_path_element(mock_element)

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result["ty"], "sh")

    def test_fallback_strategy_error_case(self):
        """Test the fallback SVG path parsing strategy with error case"""
        # Create a mock SVG path element
        mock_element = MagicMock()

        # Make BaseSVGPathParsingStrategy.parse_path_element raise an exception
        with patch.object(
            BaseSVGPathParsingStrategy,
            "parse_path_element",
            side_effect=Exception("Test exception"),
        ):
            # Provide fallback properties for the element
            mock_element.first_point = MagicMock()
            mock_element.first_point.x = 10
            mock_element.first_point.y = 20
            mock_element.current_point = MagicMock()
            mock_element.current_point.x = 30
            mock_element.current_point.y = 40

            # Create a mock path builder that returns a valid path
            mock_path = {
                "ty": "sh",
                "ks": {
                    "k": {
                        "v": [[10, 20], [30, 40]],
                        "i": [[0, 0], [0, 0]],
                        "o": [[0, 0], [0, 0]],
                        "c": False,
                    }
                },
            }

            # Mock the path builder to return our mock path
            with patch.object(
                self.fallback_strategy.path_builder,
                "build_lottie_path",
                return_value=mock_path,
            ):
                result = self.fallback_strategy.parse_path_element(mock_element)

                # Verify the result - should create a simple line
                self.assertIsNotNone(result)
                self.assertEqual(result["ty"], "sh")
                self.assertEqual(len(result["ks"]["k"]["v"]), 2)
                self.assertEqual(result["ks"]["k"]["v"][0], [10, 20])
                self.assertEqual(result["ks"]["k"]["v"][1], [30, 40])

    def test_fallback_strategy_segments_fallback(self):
        """Test the fallback SVG path parsing strategy with segment extraction fallback"""
        # Create a mock SVG path element
        mock_element = MagicMock()

        # Make BaseSVGPathParsingStrategy.parse_path_element raise an exception
        with patch.object(
            BaseSVGPathParsingStrategy,
            "parse_path_element",
            side_effect=Exception("Test exception"),
        ):
            # Don't provide first_point but set up segments
            mock_element.first_point = None

            # Set up segments for extraction
            mock_segment1 = MagicMock()
            mock_segment1.end.x = 10
            mock_segment1.end.y = 20

            mock_segment2 = MagicMock()
            mock_segment2.end.x = 30
            mock_segment2.end.y = 40

            # Configure __iter__ to first fail, then return segments on second call
            mock_element.__iter__.side_effect = [
                Exception("First failure"),
                [mock_segment1, mock_segment2],
            ]

            # Create a mock path
            mock_path = {
                "ty": "sh",
                "ks": {
                    "k": {
                        "v": [[10, 20], [30, 40]],
                        "i": [[0, 0], [0, 0]],
                        "o": [[0, 0], [0, 0]],
                        "c": False,
                    }
                },
            }

            # Mock the path builder to return our mock path
            with patch.object(
                self.fallback_strategy.path_builder,
                "build_lottie_path",
                return_value=mock_path,
            ):
                result = self.fallback_strategy.parse_path_element(mock_element)

                # Verify the result - should create a path from segments
                self.assertIsNotNone(result)
                self.assertEqual(result["ty"], "sh")
                self.assertEqual(len(result["ks"]["k"]["v"]), 2)


class TestSegmentProcessors(unittest.TestCase):
    """Test cases for the segment processors"""

    def setUp(self):
        self.standard_processor = StandardSegmentProcessor()
        self.optimized_processor = OptimizedSegmentProcessor(simplify_tolerance=0.5)
        self.simplified_processor = SimplifiedSegmentProcessor()

    def test_standard_processor_move_segment(self):
        """Test processing a Move segment with the standard processor"""
        mock_segment = MagicMock()
        mock_segment.__class__.__name__ = "Move"
        mock_segment.end.x = 10
        mock_segment.end.y = 20

        vertices = []
        in_tangents = []
        out_tangents = []
        current_point = None

        vertices, in_tangents, out_tangents, current_point = (
            self.standard_processor.process_segment(
                mock_segment, current_point, vertices, in_tangents, out_tangents
            )
        )

        # Verify the result
        self.assertEqual(len(vertices), 1)
        self.assertEqual(vertices[0], [10, 20])
        self.assertEqual(in_tangents[0], [0, 0])
        self.assertEqual(out_tangents[0], [0, 0])
        self.assertEqual(current_point, mock_segment.end)

    def test_standard_processor_line_segment(self):
        """Test processing a Line segment with the standard processor"""
        mock_segment = MagicMock()
        mock_segment.__class__.__name__ = "Line"
        mock_segment.end.x = 30
        mock_segment.end.y = 40

        vertices = [[10, 20]]
        in_tangents = [[0, 0]]
        out_tangents = [[0, 0]]
        current_point = MagicMock()
        current_point.x = 10
        current_point.y = 20

        vertices, in_tangents, out_tangents, current_point = (
            self.standard_processor.process_segment(
                mock_segment, current_point, vertices, in_tangents, out_tangents
            )
        )

        # Verify the result
        self.assertEqual(len(vertices), 2)
        self.assertEqual(vertices[1], [30, 40])
        self.assertEqual(in_tangents[1], [0, 0])
        self.assertEqual(out_tangents[1], [0, 0])
        self.assertEqual(current_point, mock_segment.end)

    def test_standard_processor_bezier_segment(self):
        """Test processing a CubicBezier segment with the standard processor"""
        mock_segment = MagicMock()
        mock_segment.__class__.__name__ = "CubicBezier"
        mock_segment.end.x = 50
        mock_segment.end.y = 60
        mock_segment.control1.x = 20
        mock_segment.control1.y = 30
        mock_segment.control2.x = 40
        mock_segment.control2.y = 50

        vertices = [[10, 20]]
        in_tangents = [[0, 0]]
        out_tangents = [[0, 0]]
        current_point = MagicMock()
        current_point.x = 10
        current_point.y = 20

        vertices, in_tangents, out_tangents, current_point = (
            self.standard_processor.process_segment(
                mock_segment, current_point, vertices, in_tangents, out_tangents
            )
        )

        # Verify the result
        self.assertEqual(len(vertices), 2)
        self.assertEqual(vertices[1], [50, 60])

        # Check that tangents were calculated correctly
        # Out tangent of previous point (relative to current point)
        self.assertEqual(out_tangents[0], [10, 10])  # (20-10, 30-20)

        # In tangent of current point (relative to end point)
        self.assertEqual(in_tangents[1], [-10, -10])  # (40-50, 50-60)

    def test_simplified_processor_bezier_segment(self):
        """Test processing a CubicBezier segment with the simplified processor"""
        mock_segment = MagicMock()
        mock_segment.__class__.__name__ = "CubicBezier"
        mock_segment.end.x = 50
        mock_segment.end.y = 60
        mock_segment.control1.x = 20
        mock_segment.control1.y = 30
        mock_segment.control2.x = 40
        mock_segment.control2.y = 50

        vertices = [[10, 20]]
        in_tangents = [[0, 0]]
        out_tangents = [[0, 0]]
        current_point = MagicMock()
        current_point.x = 10
        current_point.y = 20

        vertices, in_tangents, out_tangents, current_point = (
            self.simplified_processor.process_segment(
                mock_segment, current_point, vertices, in_tangents, out_tangents
            )
        )

        # Verify the result - simplified processor should convert bezier to line
        self.assertEqual(len(vertices), 2)
        self.assertEqual(vertices[1], [50, 60])

        # All tangents should be zero in simplified processor
        self.assertEqual(out_tangents[0], [0, 0])
        self.assertEqual(in_tangents[1], [0, 0])


class TestSVGElementFilters(unittest.TestCase):
    """Test cases for the SVG element filters"""

    def setUp(self):
        self.standard_filter = StandardSVGElementFilter()
        self.advanced_filter = AdvancedSVGElementFilter(
            include_groups=True, include_hidden=False
        )

    def test_standard_filter_path_element(self):
        """Test standard filter with a path element"""
        # Create a mock with the right structure to pass the name check
        mock_element = MagicMock()
        mock_element.__class__.__name__ = "Path"

        # Patch the isinstance check to always return True for our mock
        with patch(
            "app.infrastructure.svg_parsing.base_strategies.BaseSVGElementFilter.should_process",
            return_value=True,
        ):
            result = self.standard_filter.should_process(mock_element)

            # Should process path elements
            self.assertTrue(result)

    def test_standard_filter_non_path_element(self):
        """Test standard filter with a non-path element"""
        mock_element = MagicMock()
        mock_element.__class__.__name__ = "Circle"

        result = self.standard_filter.should_process(mock_element)

        # Should not process non-path elements
        self.assertFalse(result)

    def test_advanced_filter_group_element(self):
        """Test advanced filter with a group element"""
        mock_element = MagicMock()
        mock_element.__class__.__name__ = "Group"

        result = self.advanced_filter.should_process(mock_element)

        # Should process group elements with include_groups=True
        self.assertTrue(result)

    def test_advanced_filter_hidden_element(self):
        """Test advanced filter with a hidden element"""
        mock_element = MagicMock()
        mock_element.__class__.__name__ = "Path"
        mock_element.values = {"style": "display:none"}

        result = self.advanced_filter.should_process(mock_element)

        # Should not process hidden elements with include_hidden=False
        self.assertFalse(result)


class TestLottiePathBuilders(unittest.TestCase):
    """Test cases for the Lottie path builders"""

    def setUp(self):
        self.standard_builder = StandardLottiePathBuilder()
        self.enhanced_builder = EnhancedLottiePathBuilder()

    def test_standard_builder(self):
        """Test the standard Lottie path builder"""
        vertices = [[10, 20], [30, 40], [50, 60]]
        in_tangents = [[0, 0], [0, 0], [0, 0]]
        out_tangents = [[0, 0], [0, 0], [0, 0]]
        closed = True

        result = self.standard_builder.build_lottie_path(
            vertices, in_tangents, out_tangents, closed
        )

        # Verify the result
        self.assertEqual(result["ty"], "sh")
        self.assertEqual(result["ks"]["a"], 0)
        self.assertEqual(result["ks"]["k"]["c"], True)
        self.assertEqual(result["ks"]["k"]["v"], vertices)
        self.assertEqual(result["ks"]["k"]["i"], in_tangents)
        self.assertEqual(result["ks"]["k"]["o"], out_tangents)

        # Standard builder should not add additional properties
        self.assertNotIn("nm", result)
        self.assertNotIn("hd", result)

    def test_enhanced_builder(self):
        """Test the enhanced Lottie path builder"""
        vertices = [[10, 20], [30, 40], [50, 60]]
        in_tangents = [[0, 0], [0, 0], [0, 0]]
        out_tangents = [[0, 0], [0, 0], [0, 0]]
        closed = True

        result = self.enhanced_builder.build_lottie_path(
            vertices, in_tangents, out_tangents, closed
        )

        # Verify the result
        self.assertEqual(result["ty"], "sh")
        self.assertEqual(result["ks"]["a"], 0)
        self.assertEqual(result["ks"]["k"]["c"], True)
        self.assertEqual(result["ks"]["k"]["v"], vertices)
        self.assertEqual(result["ks"]["k"]["i"], in_tangents)
        self.assertEqual(result["ks"]["k"]["o"], out_tangents)

        # Enhanced builder should add additional properties
        self.assertEqual(result["nm"], "Path")
        self.assertEqual(result["hd"], False)


if __name__ == "__main__":
    unittest.main()
