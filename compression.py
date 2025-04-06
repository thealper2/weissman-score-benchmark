import os
import time
import gzip
import bz2
import lzma
import zipfile
import tarfile
import shutil
from pathlib import Path
from typing import Tuple
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
import tempfile
import logging


@dataclass
class CompressionResult:
    """Data class to store compression benchmark results."""

    algorithm: str
    original_size: int
    compressed_size: int
    compression_ratio: float
    compression_time: float
    weissman_score: float = 0.0


class SupportedCompressors(Enum):
    """Enum for supported compression algorithms."""

    GZIP = "gzip"
    BZIP2 = "bzip2"
    LZMA = "lzma"
    ZIP = "zip"
    TAR = "tar"


class Compressor(ABC):
    """Abstract base class for compression algorithms."""

    def __init__(self, logger: logging.Logger):
        """
        Initialize the compressor.

        Args:
            logger (logging.Logger): Logger instance
        """
        self.logger = logger

    @abstractmethod
    def compress(self, input_path: Path) -> Tuple[int, float]:
        """
        Compress the given input path and return the compressed size and time taken.

        Args:
            input_path (path): Path to the file or directory to compress

        Returns:
            Tuple[int, float]: Tuple containing compressed size in bytes and time taken in seconds
        """
        pass

    def get_size(self, path: Path) -> int:
        """
        Get the size of a file or directory.

        Args:
            path (Path): Path to the file or directory

        Returns:
            int: Size in bytes
        """
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            return sum(f.stat().st_size for f in path.glob("**/*") if f.is_file())
        else:
            return 0


class GzipCompressor(Compressor):
    """Gzip compression implementation."""

    def compress(self, input_path: Path) -> Tuple[int, float]:
        """
        Compress using gzip algorithm.

        Args:
            input_path (Path): Path to the file or directory to compress

        Returns:
            Tuple[int, float]: Tuple containing compressed size in bytes and time taken in seconds
        """
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            start_time = time.time()

            if input_path.is_file():
                with open(input_path, "rb") as f_in:
                    with gzip.open(temp_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                # For directories, create a tar.gz
                with tarfile.open(temp_path, "w:gz") as tar:
                    tar.add(input_path, arcname=input_path.name)

            compression_time = time.time() - start_time
            compressed_size = self.get_size(temp_path)

            self.logger.debug(
                f"Gzip compression completed: {compressed_size} bytes in {compression_time:.4f} seconds"
            )
            return compressed_size, compression_time

        finally:
            # Clean up temporary file
            if temp_path.exists():
                os.unlink(temp_path)


class Bzip2Compressor(Compressor):
    """Bzip2 compression implementation."""

    def compress(self, input_path: Path) -> Tuple[int, float]:
        """
        Compress using bzip2 algorithm.

        Args:
            input_path (Path): Path to the file or directory to compress

        Returns:
            Tuple[int, float]: Tuple containing compressed size in bytes and time taken in seconds
        """
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            start_time = time.time()

            if input_path.is_file():
                with open(input_path, "rb") as f_in:
                    with bz2.open(temp_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                # For directories, create a tar.bz2
                with tarfile.open(temp_path, "w:bz2") as tar:
                    tar.add(input_path, arcname=input_path.name)

            compression_time = time.time() - start_time
            compressed_size = self.get_size(temp_path)

            self.logger.debug(
                f"Bzip2 compression completed: {compressed_size} bytes in {compression_time:.4f} seconds"
            )
            return compressed_size, compression_time

        finally:
            # Clean up temporary file
            if temp_path.exists():
                os.unlink(temp_path)


class LzmaCompressor(Compressor):
    """LZMA compression implementation."""

    def compress(self, input_path: Path) -> Tuple[int, float]:
        """
        Compress using LZMA algorithm.

        Args:
            input_path: Path to the file or directory to compress

        Returns:
            Tuple containing compressed size in bytes and time taken in seconds
        """
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            start_time = time.time()

            if input_path.is_file():
                with open(input_path, "rb") as f_in:
                    with lzma.open(temp_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                # For directories, create a tar.xz
                with tarfile.open(temp_path, "w:xz") as tar:
                    tar.add(input_path, arcname=input_path.name)

            compression_time = time.time() - start_time
            compressed_size = self.get_size(temp_path)

            self.logger.debug(
                f"LZMA compression completed: {compressed_size} bytes in {compression_time:.4f} seconds"
            )
            return compressed_size, compression_time

        finally:
            # Clean up temporary file
            if temp_path.exists():
                os.unlink(temp_path)


class ZipCompressor(Compressor):
    """ZIP compression implementation."""

    def compress(self, input_path: Path) -> Tuple[int, float]:
        """
        Compress using ZIP algorithm.

        Args:
            input_path: Path to the file or directory to compress

        Returns:
            Tuple containing compressed size in bytes and time taken in seconds
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
            temp_path = Path(temp_file.name)

        try:
            start_time = time.time()

            with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                if input_path.is_file():
                    zipf.write(input_path, arcname=input_path.name)
                else:
                    for file_path in input_path.glob("**/*"):
                        if file_path.is_file():
                            relative_path = file_path.relative_to(input_path.parent)
                            zipf.write(file_path, arcname=relative_path)

            compression_time = time.time() - start_time
            compressed_size = self.get_size(temp_path)

            self.logger.debug(
                f"ZIP compression completed: {compressed_size} bytes in {compression_time:.4f} seconds"
            )
            return compressed_size, compression_time

        finally:
            # Clean up temporary file
            if temp_path.exists():
                os.unlink(temp_path)


class TarCompressor(Compressor):
    """TAR compression implementation (no compression, just archiving)."""

    def compress(self, input_path: Path) -> Tuple[int, float]:
        """
        Archive using TAR format (no compression).

        Args:
            input_path (Path): Path to the file or directory to compress

        Returns:
            Tuple[int, float]: Tuple containing archived size in bytes and time taken in seconds
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tar") as temp_file:
            temp_path = Path(temp_file.name)

        try:
            start_time = time.time()

            with tarfile.open(temp_path, "w") as tar:
                tar.add(input_path, arcname=input_path.name)

            compression_time = time.time() - start_time
            compressed_size = self.get_size(temp_path)

            self.logger.debug(
                f"TAR archiving completed: {compressed_size} bytes in {compression_time:.4f} seconds"
            )
            return compressed_size, compression_time

        finally:
            # Clean up temporary file
            if temp_path.exists():
                os.unlink(temp_path)


class CompressorFactory:
    """Factory class for creating compressor instances."""

    @staticmethod
    def get_compressor(
        algorithm: SupportedCompressors, logger: logging.Logger
    ) -> Compressor:
        """
        Get a compressor instance for the specified algorithm.

        Args:
            algorithm (SupportedCompressors): The compression algorithm to use
            logger (logging.Logger): Logger instance

        Returns:
            Compressor: Compressor instance

        Raises:
            ValueError: If the algorithm is not supported
        """
        compressors = {
            SupportedCompressors.GZIP: GzipCompressor,
            SupportedCompressors.BZIP2: Bzip2Compressor,
            SupportedCompressors.LZMA: LzmaCompressor,
            SupportedCompressors.ZIP: ZipCompressor,
            SupportedCompressors.TAR: TarCompressor,
        }

        if algorithm not in compressors:
            raise ValueError(f"Unsupported compression algorithm: {algorithm}")

        return compressors[algorithm](logger)
