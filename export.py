import json
import csv
import xml.dom.minidom
import html
from pathlib import Path
from typing import List
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import asdict

from compression import CompressionResult


class SupportedFormats(Enum):
    """Enum for supported export formats."""

    JSON = "json"
    XML = "xml"
    CSV = "csv"
    HTML = "html"


class Exporter(ABC):
    """Abstract base class for exporters."""

    @abstractmethod
    def export(self, results: List[CompressionResult], output_path: Path) -> None:
        """
        Export results to the specified output path.

        Args:
            results (List[CompressionResult]): List of compression results
            output_path (Path): Path to write the output to
        """
        pass


class JsonExporter(Exporter):
    """JSON exporter implementation."""

    def export(self, results: List[CompressionResult], output_path: Path) -> None:
        """
        Export results to JSON format.

        Args:
            results (List[CompressionResult]): List of compression results
            output_path (Path): Path to write the JSON file to
        """
        data = [asdict(result) for result in results]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


class XmlExporter(Exporter):
    """XML exporter implementation."""

    def export(self, results: List[CompressionResult], output_path: Path) -> None:
        """
        Export results to XML format.

        Args:
            results (List[CompressionResult]): List of compression results
            output_path (Path): Path to write the XML file to
        """
        doc = xml.dom.minidom.getDOMImplementation().createDocument(
            None, "CompressionResults", None
        )
        root = doc.documentElement

        for result in results:
            result_elem = doc.createElement("Result")
            root.appendChild(result_elem)

            for key, value in asdict(result).items():
                elem = doc.createElement(key)
                result_elem.appendChild(elem)
                text = doc.createTextNode(str(value))
                elem.appendChild(text)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(doc.toprettyxml(indent="  "))


class CsvExporter(Exporter):
    """CSV exporter implementation."""

    def export(self, results: List[CompressionResult], output_path: Path) -> None:
        """
        Export results to CSV format.

        Args:
            results (List[CompressionResult]): List of compression results
            output_path (Path): Path to write the CSV file to
        """
        if not results:
            return

        fieldnames = asdict(results[0]).keys()

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                writer.writerow(asdict(result))


class HtmlExporter(Exporter):
    """HTML exporter implementation."""

    def export(self, results: List[CompressionResult], output_path: Path) -> None:
        """
        Export results to HTML format.

        Args:
            results (List[CompressionResult]): List of compression results
            output_path (Path): Path to write the HTML file to
        """
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Compression Benchmark Results</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                table { border-collapse: collapse; width: 100%; margin-top: 20px; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
                tr:hover { background-color: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Compression Benchmark Results</h1>
                <table>
                    <thead>
                        <tr>
                            <th>Algorithm</th>
                            <th>Original Size</th>
                            <th>Compressed Size</th>
                            <th>Compression Ratio</th>
                            <th>Compression Time (s)</th>
                            <th>Weissman Score</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        # Sort results by Weissman score (descending)
        sorted_results = sorted(results, key=lambda r: r.weissman_score, reverse=True)

        for result in sorted_results:
            original_size = self._format_size(result.original_size)
            compressed_size = self._format_size(result.compressed_size)

            html_content += f"""
                        <tr>
                            <td>{html.escape(result.algorithm)}</td>
                            <td>{original_size}</td>
                            <td>{compressed_size}</td>
                            <td>{result.compression_ratio:.2f}</td>
                            <td>{result.compression_time:.4f}</td>
                            <td>{result.weissman_score:.4f}</td>
                        </tr>
            """

        html_content += """
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

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


class ExportFactory:
    """Factory class for creating exporter instances."""

    @staticmethod
    def get_exporter(format_type: SupportedFormats) -> Exporter:
        """
        Get an exporter instance for the specified format.

        Args:
            format_type (SupportedFormats): The export format to use

        Returns:
            Exporter: Exporter instance

        Raises:
            ValueError: If the format is not supported
        """
        exporters = {
            SupportedFormats.JSON: JsonExporter,
            SupportedFormats.XML: XmlExporter,
            SupportedFormats.CSV: CsvExporter,
            SupportedFormats.HTML: HtmlExporter,
        }

        if format_type not in exporters:
            raise ValueError(f"Unsupported export format: {format_type}")

        return exporters[format_type]()
