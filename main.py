import sys
import argparse
from pathlib import Path
from typing import List

from rich.console import Console

from compression import SupportedCompressors
from export import ExportFactory, SupportedFormats
from benchmark import CompressionBenchmark
from utils import validate_input_path, setup_logger

# Initialize Rich console
console = Console()


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Benchmark compression algorithms and calculate Weissman scores",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("path", type=str, help="Path to file or directory to compress")

    parser.add_argument(
        "--algorithm",
        "-a",
        type=str,
        choices=[algo.value for algo in SupportedCompressors] + ["all"],
        default="all",
        help="Compression algorithm to benchmark (or 'all' for all supported algorithms)",
    )

    parser.add_argument(
        "--alpha",
        type=float,
        default=1.0,
        help="Alpha scaling constant for Weissman score calculation",
    )

    parser.add_argument(
        "--export",
        "-e",
        type=str,
        choices=[fmt.value for fmt in SupportedFormats],
        help="Export results in the specified format",
    )

    parser.add_argument(
        "--output", "-o", type=str, help="Output file path for exported results"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    # Validate that output is provided if export is specified
    if args.export and not args.output:
        parser.error("--output is required when --export is specified")

    return args


def main() -> int:
    """
    Main function that orchestrates the compression benchmark process.

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        # Parse arguments
        args = parse_arguments()

        # Setup logger
        logger = setup_logger(verbose=args.verbose)
        logger.info("Starting compression benchmark")

        # Validate input path
        input_path = validate_input_path(args.path)
        if not input_path:
            console.print(f"[bold red]Error:[/] Invalid path: {args.path}")
            return 1

        # Determine which algorithms to benchmark
        algorithms: List[SupportedCompressors] = []
        if args.algorithm == "all":
            algorithms = list(SupportedCompressors)
        else:
            algorithms = [SupportedCompressors(args.algorithm)]

        # Create benchmark instance
        benchmark = CompressionBenchmark(
            input_path=input_path, alpha=args.alpha, console=console, logger=logger
        )

        # Run benchmarks
        results = benchmark.run_benchmarks(algorithms)

        # Export results if requested
        if args.export:
            export_format = SupportedFormats(args.export)
            exporter = ExportFactory.get_exporter(export_format)
            exporter.export(results, Path(args.output))
            console.print(f"[green]Results exported to:[/] {args.output}")

        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]Process interrupted by user.[/]")
        return 130
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
