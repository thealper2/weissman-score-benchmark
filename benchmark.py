import math
import logging
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn

from compression import CompressorFactory, SupportedCompressors, CompressionResult


class WeissmanScoreCalculator:
    """
    Calculator for Weissman Score based on compression ratio and time.

    The Weissman Score is calculated as:
    alpha * (reference_r / target_r) * (log(target_T) / log(reference_T))

    Where:
    - alpha: scaling constant
    - reference_r: compression ratio for reference algorithm (gzip)
    - reference_T: time required to compress for reference algorithm (gzip)
    - target_r: compression ratio for target algorithm
    - target_T: time required to compress for target algorithm
    """

    def __init__(self, alpha: float = 1.0):
        """
        Initialize the Weissman Score calculator.

        Args:
            alpha: Scaling constant for the Weissman score
        """
        self.alpha = alpha

    def calculate(
        self,
        target_ratio: float,
        target_time: float,
        reference_ratio: float,
        reference_time: float,
    ) -> float:
        """
        Calculate Weissman Score.

        Args:
            target_ratio (float): Compression ratio of the target algorithm
            target_time (float): Time taken by the target algorithm
            reference_ratio (float): Compression ratio of the reference algorithm (gzip)
            reference_time (float): Time taken by the reference algorithm (gzip)

        Returns:
            float: Weissman Score
        """
        # Avoid division by zero or log of zero/negative numbers
        if (
            target_ratio <= 0.0
            or reference_ratio <= 0.0
            or target_time <= 0.0
            or reference_time <= 0.0
        ):
            return 0.0

        # Calculate Weissman Score
        compression_term = reference_ratio / target_ratio
        time_term = math.log(target_time) / math.log(reference_time)

        return self.alpha * compression_term * time_term


class CompressionBenchmark:
    """Benchmarks compression algorithms and calculates Weissman scores."""

    def __init__(
        self,
        input_path: Path,
        alpha: float = 1.0,
        console: Optional[Console] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the compression benchmark.

        Args:
            input_path (Path): Path to the file or directory to compress
            alpha (float): Scaling constant for Weissman score calculation
            console (Optional[Console]): Rich console instance for output
            logger (Optional[logging.logger]): Logger instance
        """
        self.input_path = input_path
        self.weissman_calculator = WeissmanScoreCalculator(alpha)
        self.console = console or Console()
        self.logger = logger or logging.getLogger(__name__)

        # Validate input path
        if not self.input_path.exists():
            raise FileNotFoundError(f"Path does not exist: {self.input_path}")

    def run_benchmarks(
        self, algorithms: List[SupportedCompressors]
    ) -> List[CompressionResult]:
        """
        Run benchmarks for the specified compression algorithms.

        Args:
            algorithms (List[SupportedCompressors]): List of compression algorithms to benchmark

        Returns:
            List[CompressionResult]: List of compression results
        """
        results: List[CompressionResult] = []
        original_size = self._get_original_size()

        self.console.print(
            f"[bold blue]Benchmarking compression algorithms for:[/] {self.input_path}"
        )
        self.console.print(
            f"Original size: [green]{self._format_size(original_size)}[/]"
        )

        # Create progress bar
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:
            benchmark_task = progress.add_task(
                "[red]Running benchmarks...", total=len(algorithms)
            )

            # Get reference (gzip) results first if it's in the list
            reference_result = None
            for algo in algorithms.copy():
                if algo == SupportedCompressors.GZIP:
                    reference_result = self._benchmark_algorithm(algo, original_size)
                    results.append(reference_result)
                    algorithms.remove(algo)
                    progress.update(benchmark_task, advance=1)
                    break

            # If gzip wasn't in the list, run it separately for reference
            if reference_result is None:
                self.logger.info("Running gzip as reference algorithm")
                reference_result = self._benchmark_algorithm(
                    SupportedCompressors.GZIP, original_size
                )

            # Run benchmarks for remaining algorithms
            for algorithm in algorithms:
                result = self._benchmark_algorithm(algorithm, original_size)

                # Calculate Weissman score
                result.weissman_score = self.weissman_calculator.calculate(
                    target_ratio=result.compression_ratio,
                    target_time=result.compression_time,
                    reference_ratio=reference_result.compression_ratio,
                    reference_time=reference_result.compression_time,
                )

                results.append(result)
                progress.update(benchmark_task, advance=1)

        # Add Weissman score to reference result if it's in the results list
        for result in results:
            if result.algorithm == SupportedCompressors.GZIP.value:
                result.weissman_score = 1.0  # By definition

        # Display results table
        self._display_results_table(results)

        return results

    def _benchmark_algorithm(
        self, algorithm: SupportedCompressors, original_size: int
    ) -> CompressionResult:
        """
        Benchmark a single compression algorithm.

        Args:
            algorithm (SupportedCompressors): Compression algorithm to benchmark
            original_size (int): Original size of the input

        Returns:
            CompressionResult: Compression result
        """
        self.logger.info(f"Benchmarking {algorithm.value}")

        compressor = CompressorFactory.get_compressor(algorithm, self.logger)
        compressed_size, compression_time = compressor.compress(self.input_path)

        # Calculate compression ratio (original / compressed)
        compression_ratio = (
            original_size / compressed_size if compressed_size > 0 else 0
        )

        return CompressionResult(
            algorithm=algorithm.value,
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            compression_time=compression_time,
        )

    def _get_original_size(self) -> int:
        """
        Get the original size of the input path.

        Returns:
            int: Size in bytes
        """
        if self.input_path.is_file():
            return self.input_path.stat().st_size
        elif self.input_path.is_dir():
            total_size = 0
            for file_path in self.input_path.glob("**/*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        else:
            return 0

    def _display_results_table(self, results: List[CompressionResult]) -> None:
        """
        Display the benchmark results in a table.

        Args:
            results (List[CompressionResult]): List of compression results
        """
        table = Table(title="Compression Benchmark Results")

        table.add_column("Algorithm", style="cyan")
        table.add_column("Original Size", style="green", justify="right")
        table.add_column("Compressed Size", style="green", justify="right")
        table.add_column("Ratio", style="magenta", justify="right")
        table.add_column("Time (s)", style="yellow", justify="right")
        table.add_column("Weissman Score", style="red", justify="right")

        # Sort results by Weissman score (descending)
        sorted_results = sorted(results, key=lambda r: r.weissman_score, reverse=True)

        for result in sorted_results:
            table.add_row(
                result.algorithm,
                self._format_size(result.original_size),
                self._format_size(result.compressed_size),
                f"{result.compression_ratio:.2f}",
                f"{result.compression_time:.4f}",
                f"{result.weissman_score:.4f}",
            )

        self.console.print(table)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """
        Format size in bytes to a human-readable format.

        Args:
            size_bytes (int): Size in bytes

        Returns:
            str: Formatted size string
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
