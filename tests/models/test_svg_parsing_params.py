import unittest
from app.models.svg_parsing_params import (
    SVGParsingParams,
    SVGParsingParamBuilder,
    SVGParsingStrategy,
)


class TestSVGParsingParams(unittest.TestCase):
    """Test cases for the SVGParsingParams class"""

    def test_default_params(self):
        """Test default parameter values"""
        params = SVGParsingParams(svg_path="test.svg")

        self.assertEqual(params.svg_path, "test.svg")
        self.assertEqual(params.strategy, SVGParsingStrategy.STANDARD)
        self.assertIsNone(params.simplify_tolerance)
        self.assertFalse(params.ignore_transforms)
        self.assertTrue(params.extract_colors)  # Default is True in the implementation
        self.assertIsNone(params.max_paths)
        self.assertEqual(
            params.error_handling, "raise"
        )  # Default is 'raise' in the implementation
        self.assertIsNone(params.metadata)  # Default is None in the implementation

    def test_custom_params(self):
        """Test custom parameter values"""
        params = SVGParsingParams(
            svg_path="test.svg",
            strategy=SVGParsingStrategy.OPTIMIZED,
            simplify_tolerance=0.5,
            ignore_transforms=True,
            extract_colors=True,
            max_paths=10,
            error_handling="raise",
            metadata={"test": "value"},
        )

        self.assertEqual(params.svg_path, "test.svg")
        self.assertEqual(params.strategy, SVGParsingStrategy.OPTIMIZED)
        self.assertEqual(params.simplify_tolerance, 0.5)
        self.assertTrue(params.ignore_transforms)
        self.assertTrue(params.extract_colors)
        self.assertEqual(params.max_paths, 10)
        self.assertEqual(params.error_handling, "raise")
        self.assertEqual(params.metadata, {"test": "value"})

    def test_invalid_error_handling(self):
        """Test invalid error_handling value"""
        with self.assertRaises(ValueError):
            SVGParsingParams(svg_path="test.svg", error_handling="invalid")

    def test_invalid_simplify_tolerance(self):
        """Test invalid simplify_tolerance value"""
        with self.assertRaises(ValueError):
            SVGParsingParams(svg_path="test.svg", simplify_tolerance=-0.5)


class TestSVGParsingParamBuilder(unittest.TestCase):
    """Test cases for the SVGParsingParamBuilder class"""

    def test_builder_default(self):
        """Test builder with default values"""
        builder = SVGParsingParamBuilder()
        builder.with_svg_path("test.svg")
        params = builder.build()

        self.assertEqual(params.svg_path, "test.svg")
        self.assertEqual(params.strategy, SVGParsingStrategy.STANDARD)
        self.assertIsNone(params.simplify_tolerance)
        self.assertFalse(params.ignore_transforms)
        self.assertTrue(params.extract_colors)  # Default is True in the implementation
        self.assertIsNone(params.max_paths)
        self.assertEqual(
            params.error_handling, "raise"
        )  # Default is 'raise' in the implementation
        self.assertIsNone(params.metadata)  # Default is None in the implementation

    def test_builder_fluent_interface(self):
        """Test builder's fluent interface"""
        params = (
            SVGParsingParamBuilder()
            .with_svg_path("test.svg")
            .with_strategy(SVGParsingStrategy.OPTIMIZED)
            .with_simplify_tolerance(0.5)
            .with_ignore_transforms(True)
            .with_extract_colors(True)
            .with_max_paths(10)
            .with_error_handling("raise")
            .with_metadata({"test": "value"})
            .build()
        )

        self.assertEqual(params.svg_path, "test.svg")
        self.assertEqual(params.strategy, SVGParsingStrategy.OPTIMIZED)
        self.assertEqual(params.simplify_tolerance, 0.5)
        self.assertTrue(params.ignore_transforms)
        self.assertTrue(params.extract_colors)
        self.assertEqual(params.max_paths, 10)
        self.assertEqual(params.error_handling, "raise")
        self.assertEqual(params.metadata, {"test": "value"})

    def test_builder_chaining(self):
        """Test builder with method chaining in different order"""
        builder = SVGParsingParamBuilder()

        # Chain methods in a different order
        builder.with_svg_path("test.svg")
        builder.with_metadata({"test": "value"})
        builder.with_max_paths(10)
        builder.with_strategy(SVGParsingStrategy.OPTIMIZED)

        params = builder.build()

        self.assertEqual(params.svg_path, "test.svg")
        self.assertEqual(params.strategy, SVGParsingStrategy.OPTIMIZED)
        self.assertEqual(params.max_paths, 10)
        self.assertEqual(params.metadata, {"test": "value"})

    def test_builder_invalid_values(self):
        """Test builder with invalid values"""
        builder = SVGParsingParamBuilder()
        builder.with_svg_path("test.svg")

        # Invalid error_handling
        with self.assertRaises(ValueError):
            builder.with_error_handling("invalid").build()

        # Reset builder
        builder = SVGParsingParamBuilder()
        builder.with_svg_path("test.svg")

        # Invalid simplify_tolerance
        with self.assertRaises(ValueError):
            builder.with_simplify_tolerance(-0.5).build()


if __name__ == "__main__":
    unittest.main()
