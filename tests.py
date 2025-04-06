import unittest
import tempfile
import os
from pathlib import Path
import json

from compression import (
    CompressionResult,
    SupportedCompressors,
    GzipCompressor,
    CompressorFactory,
)
from export import SupportedFormats, ExportFactory
from benchmark import WeissmanScoreCalculator
from utils import validate_input_path, setup_logger

# Set up logger for tests
logger = setup_logger(verbose=False)


class TestCompression(unittest.TestCase):
    """Test cases for compression module."""

    def setUp(self):
        """Set up test files and directories."""
        # Create a temporary test file
        self.test_file = tempfile.NamedTemporaryFile(delete=False)
        self.test_file.write(b"a" * 10000)  # 10 KB of data
        self.test_file.close()
        self.test_file_path = Path(self.test_file.name)

        # Create a temporary test directory with files
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_dir_path = Path(self.test_dir.name)

        # Create some files in the test directory
        for i in range(5):
            with open(self.test_dir_path / f"file{i}.txt", "wb") as f:
                f.write(b"b" * 1000)  # 1 KB of data per file

    def tearDown(self):
        """Clean up test files and directories."""
        if self.test_file_path.exists():
            os.unlink(self.test_file_path)

        self.test_dir.cleanup()

    def test_gzip_compression(self):
        """Test gzip compression on a file."""
        compressor = GzipCompressor(logger)
        compressed_size, compression_time = compressor.compress(self.test_file_path)

        self.assertLess(compressed_size, self.test_file_path.stat().st_size)
        self.assertGreater(compression_time, 0)

    def test_compressor_factory(self):
        """Test that the compressor factory creates the correct compressors."""
        for algo in SupportedCompressors:
            compressor = CompressorFactory.get_compressor(algo, logger)
            self.assertIsNotNone(compressor)


class TestWeissmanScore(unittest.TestCase):
    """Test cases for Weissman score calculation."""

    def test_weissman_calculation(self):
        """Test basic Weissman score calculation."""
        calculator = WeissmanScoreCalculator(alpha=1.0)

        # Equal performance should give a score of 1.0
        score = calculator.calculate(
            target_ratio=2.0, target_time=1.0, reference_ratio=2.0, reference_time=1.0
        )
        self.assertAlmostEqual(score, 1.0)

        # Better compression ratio should increase the score
        score = calculator.calculate(
            target_ratio=4.0,  # Better (higher) ratio
            target_time=1.0,
            reference_ratio=2.0,
            reference_time=1.0,
        )
        self.assertLess(score, 1.0)  # Score should be less than 1.0

        # Edge cases - should return 0
        score = calculator.calculate(
            target_ratio=0.0, target_time=1.0, reference_ratio=2.0, reference_time=1.0
        )
        self.assertEqual(score, 0.0)


class TestExport(unittest.TestCase):
    """Test cases for export module."""

    def setUp(self):
        """Set up test results."""
        self.results = [
            CompressionResult(
                algorithm="gzip",
                original_size=10000,
                compressed_size=5000,
                compression_ratio=2.0,
                compression_time=0.5,
                weissman_score=1.0,
            ),
            CompressionResult(
                algorithm="bzip2",
                original_size=10000,
                compressed_size=4000,
                compression_ratio=2.5,
                compression_time=0.7,
                weissman_score=0.8,
            ),
        ]

    def test_json_export(self):
        """Test exporting to JSON format."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            output_path = Path(temp_file.name)

        try:
            exporter = ExportFactory.get_exporter(SupportedFormats.JSON)
            exporter.export(self.results, output_path)

            # Verify the JSON file
            with open(output_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["algorithm"], "gzip")
            self.assertEqual(data[1]["algorithm"], "bzip2")
        finally:
            if output_path.exists():
                os.unlink(output_path)

    def test_export_factory(self):
        """Test that the export factory creates the correct exporters."""
        for fmt in SupportedFormats:
            exporter = ExportFactory.get_exporter(fmt)
            self.assertIsNotNone(exporter)


class TestUtils(unittest.TestCase):
    """Test cases for utilities module."""

    def test_validate_input_path(self):
        """Test input path validation."""
        # Valid file path
        with tempfile.NamedTemporaryFile() as temp_file:
            path = validate_input_path(temp_file.name)
            self.assertIsNotNone(path)
            self.assertTrue(path.is_file())

        # Valid directory path
        with tempfile.TemporaryDirectory() as temp_dir:
            path = validate_input_path(temp_dir)
            self.assertIsNotNone(path)
            self.assertTrue(path.is_dir())

        # Invalid path
        path = validate_input_path("/nonexistent/path/that/does/not/exist")
        self.assertIsNone(path)


if __name__ == "__main__":
    unittest.main()
