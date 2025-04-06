# Compression Benchmark Tool

A Python tool to benchmark various compression algorithms (gzip, bzip2, lzma, zip, tar) against files or directories and calculate Weissman scores.

## :dart: Features

- Benchmarks multiple compression algorithms: gzip, bzip2, lzma, zip, tar
- Calculates Weissman scores based on compression ratio and time
- Exports results in various formats: JSON, XML, CSV, HTML
- Uses Rich library for beautiful terminal output
- Supports compression of files and directories

## :hammer_and_wrench: Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/thealper2/weissman-score-benchmark.git
cd weissman-score-benchmark
pip install -r requirements.txt
```

## :joystick: Usage

```bash
python main.py <path> [options]
```

### Command-line Arguments

- `path`: Path to file or directory to compress
- `--algorithm`, `-a`: Compression algorithm to benchmark (or 'all' for all supported algorithms)
- `--alpha`: Alpha scaling constant for Weissman score calculation
- `--export`, `-e`: Export results in the specified format (json, xml, csv, html)
- `--output`, `-o`: Output file path for exported results
- `--verbose`, `-v`: Enable verbose output

### Requirements

- Python 3.8+
- rich
- pydantic

### Running Tests

```bash
python -m unittest tests.py
```

## :handshake: Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch for your feature (git checkout -b feature/your-feature)
3. Commit your changes (git commit -am 'Add some feature')
4. Push to the branch (git push origin feature/your-feature)
5. Create a new Pull Request

## :scroll: License

This project is licensed under the MIT License - see the LICENSE file for details.