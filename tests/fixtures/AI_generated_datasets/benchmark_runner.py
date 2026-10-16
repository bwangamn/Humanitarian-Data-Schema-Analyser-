"""Run repeatable end-to-end benchmarks for the generated fixture datasets.

Usage (from the project root):
    python tests/fixtures/AI_generated_datasets/benchmark_runner.py

The runner discovers ``benchmark_*`` CSV, JSON, XML, XLS, and XLSX files below
this directory.  Each run performs the same parse, profile, schema-generation,
and HTML-report generation steps as the ``hds-analyzer analyze`` command.  HTML
reports are written to a temporary directory and discarded after benchmarking.
"""

from __future__ import annotations

import argparse
import ctypes
import os
import platform
import statistics
import sys
import tempfile
import time
from pathlib import Path
from typing import Iterable


DATASET_DIRECTORY = Path(__file__).resolve().parent
PROJECT_ROOT = DATASET_DIRECTORY.parents[2]
SUPPORTED_EXTENSIONS = {".csv", ".json", ".xml", ".xls", ".xlsx"}

# Allow this script to run directly from a source checkout without requiring a
# separate editable installation of the package.
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from humanitarian_schema_analyzer.parsers.factory import ParserFactory
from humanitarian_schema_analyzer.profiling.profiler import DataProfiler
from humanitarian_schema_analyzer.reports.html_report import HTMLReportGenerator
from humanitarian_schema_analyzer.schema.schema_builder import SchemaBuilder


def format_bytes(byte_count: int) -> str:
    """Return a compact binary-size representation."""
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    size = float(byte_count)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{byte_count} B"


def get_total_ram_bytes() -> int | None:
    """Read physical memory without adding a third-party dependency."""
    if os.name == "nt":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_ulong),
                ("memory_load", ctypes.c_ulong),
                ("total_phys", ctypes.c_ulonglong),
                ("avail_phys", ctypes.c_ulonglong),
                ("total_page_file", ctypes.c_ulonglong),
                ("avail_page_file", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong),
                ("avail_virtual", ctypes.c_ulonglong),
                ("avail_extended_virtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.total_phys)
        return None

    try:
        return int(os.sysconf("SC_PAGE_SIZE")) * int(os.sysconf("SC_PHYS_PAGES"))
    except (AttributeError, OSError, ValueError):
        return None


def print_machine_specs() -> None:
    """Print the environment details needed to interpret timing results."""
    processor = platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "Unknown CPU")
    ram = get_total_ram_bytes()

    print("Machine specifications")
    print(f"  OS: {platform.platform()}")
    print(f"  CPU: {processor}")
    print(f"  Logical CPU cores: {os.cpu_count() or 'Unknown'}")
    print(f"  RAM: {format_bytes(ram) if ram is not None else 'Unknown'}")
    print()


def find_benchmark_files(directory: Path) -> list[Path]:
    """Find supported files named ``benchmark_*`` anywhere below *directory*."""
    return sorted(
        (
            path
            for path in directory.rglob("benchmark_*")
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ),
        key=lambda path: path.as_posix().lower(),
    )


def analyze_once(file_path: Path, report_path: Path) -> float:
    """Run the complete analyzer pipeline once and return elapsed seconds."""
    started_at = time.perf_counter()

    parser = ParserFactory.get_parser(str(file_path))
    parsed_dataset = parser.parse()
    unified_schema = DataProfiler(parsed_dataset).profile()
    json_schema = SchemaBuilder(unified_schema).build()
    HTMLReportGenerator(unified_schema, json_schema).generate(str(report_path))

    return time.perf_counter() - started_at


def benchmark_file(file_path: Path, runs: int, reports_directory: Path) -> list[float]:
    """Benchmark one input file repeatedly, storing transient reports only."""
    timings: list[float] = []
    for run_number in range(1, runs + 1):
        report_path = reports_directory / f"{file_path.stem}-run-{run_number}.html"
        elapsed = analyze_once(file_path, report_path)
        timings.append(elapsed)
        print(f"    run {run_number}/{runs}: {elapsed:.3f} s")
    return timings


def print_result(file_path: Path, timings: Iterable[float]) -> None:
    """Print the file size and aggregate execution-time metrics."""
    results = list(timings)
    relative_path = file_path.relative_to(DATASET_DIRECTORY)
    print(f"  File: {relative_path}")
    print(f"  Size: {format_bytes(file_path.stat().st_size)} ({file_path.stat().st_size:,} bytes)")
    print(f"  Mean execution time ({len(results)} runs): {statistics.mean(results):.3f} s")
    print(f"  Minimum / maximum: {min(results):.3f} s / {max(results):.3f} s")
    if len(results) > 1:
        print(f"  Standard deviation: {statistics.stdev(results):.3f} s")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark generated analyzer fixtures.")
    parser.add_argument(
        "--runs",
        type=int,
        default=5,
        help="Number of end-to-end runs for each file (default: 5).",
    )
    arguments = parser.parse_args()

    if arguments.runs < 1:
        parser.error("--runs must be at least 1")

    files = find_benchmark_files(DATASET_DIRECTORY)
    if not files:
        print(f"No benchmark files found below {DATASET_DIRECTORY}", file=sys.stderr)
        return 1

    print_machine_specs()
    print(f"Benchmarking {len(files)} file(s), {arguments.runs} run(s) each.\n")

    with tempfile.TemporaryDirectory(prefix="hds-analyzer-benchmark-") as temporary_directory:
        reports_directory = Path(temporary_directory)
        for file_path in files:
            print(f"Running: {file_path.relative_to(DATASET_DIRECTORY)}")
            try:
                timings = benchmark_file(file_path, arguments.runs, reports_directory)
            except Exception as error:
                print(f"  FAILED: {error}\n", file=sys.stderr)
                continue
            print_result(file_path, timings)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
