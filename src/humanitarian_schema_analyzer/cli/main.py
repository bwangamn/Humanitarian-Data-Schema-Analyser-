import json
from pathlib import Path
import typer
from typing import Any, Dict, Optional

from ..parsers.factory import ParserFactory
from ..profiling.profiler import DataProfiler
from ..schema.schema_builder import SchemaBuilder
from ..schema.unifier import load_field_mapping, unify_schemas
from ..reports.html_report import HTMLReportGenerator

app = typer.Typer(
    help="Humanitarian Data Schema Analyser: Unified Schema Profiling and Standardisation CLI."
)


@app.callback()
def main() -> None:
    """Analyze humanitarian datasets from the command line."""
    pass


@app.command()
def analyze(
    file: str = typer.Argument(..., help="Path to the dataset file (CSV, JSON, XML, Excel/XLSForm)."),
    output: str = typer.Option("report.html", "--output", "-o", help="Path to save the generated HTML report."),
    schema_output: Optional[str] = typer.Option(None, "--schema-output", "-s", help="Optional path to export the raw JSON Schema file."),
    format: Optional[str] = typer.Option(None, "--format", "-f", help="Explicit format override (csv, json, xml, xlsform).")
) -> None:
    """
    Analyze, profile, and standardise a humanitarian dataset.
    """
    typer.echo(f"Analyzing dataset: {file}")

    try:
        # 1. Select Parser & Parse Data
        parser = ParserFactory.get_parser(file, format_hint=format)
        parsed_dataset = parser.parse()

        typer.echo(
            f"Successfully parsed as {parsed_dataset.format_name} format: "
            f"{len(parsed_dataset.df)} rows, {len(parsed_dataset.df.columns)} columns."
        )

        if parsed_dataset.hxl_tags:
            typer.echo(f"Detected {len(parsed_dataset.hxl_tags)} HXL semantic tags.")

        # 2. Statistical Data Profiling
        typer.echo("Running statistical profiling engine...")
        profiler = DataProfiler(parsed_dataset)
        unified_schema = profiler.profile()

        # 3. Build Standardized JSON Schema
        typer.echo("Generating Draft 2020-12 JSON Schema...")
        schema_builder = SchemaBuilder(unified_schema)
        json_schema = schema_builder.build()

        # Export raw JSON Schema if requested
        if schema_output:
            with open(schema_output, "w", encoding="utf-8") as f:
                json.dump(json_schema, f, indent=4)
            typer.echo(f"Exported JSON Schema to: {schema_output}")

        # 4. Generate Interactive HTML Report
        typer.echo("Generating interactive HTML dashboard...")
        report_generator = HTMLReportGenerator(unified_schema, json_schema)
        report_generator.generate(output)

        typer.echo(f"Analysis complete! Report saved to: {output}")

    except Exception as error:
        typer.echo(f"Error during analysis: {error}", err=True)
        raise typer.Exit(code=1)


def _load_schema(path: Path) -> Dict[str, Any]:
    """Load a JSON Schema document from an existing file."""
    if not path.is_file():
        raise FileNotFoundError(f"Schema file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as schema_file:
            schema = json.load(schema_file)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in '{path}': {error.msg}") from error
    except OSError as error:
        raise OSError(f"Could not read schema file '{path}': {error}") from error

    if not isinstance(schema, dict):
        raise ValueError(f"Schema '{path}' must contain a JSON object.")
    return schema


@app.command(name="unify")
def unify(
    schema1_path: Path = typer.Argument(..., help="Path to the first JSON Schema file."),
    schema2_path: Path = typer.Argument(..., help="Path to the second JSON Schema file."),
    mapping: Optional[Path] = typer.Option(
        None,
        "--mapping",
        "-m",
        help="CSV file with two columns (first-schema field, second-schema field) naming fields to merge.",
    ),
) -> None:
    """Merge two JSON Schema Draft 2020-12 files into one unified schema."""
    try:
        schema1 = _load_schema(schema1_path)
        schema2 = _load_schema(schema2_path)
        field_mapping = load_field_mapping(mapping) if mapping else None
        unified_schema, warnings = unify_schemas(schema1, schema2, field_mapping)

        output_path = Path.cwd() / f"{schema1_path.stem}_{schema2_path.stem}_unified.json"
        with output_path.open("w", encoding="utf-8") as output_file:
            json.dump(unified_schema, output_file, indent=2)
            output_file.write("\n")
    except (FileNotFoundError, OSError, ValueError, TypeError) as error:
        typer.secho(f"Error: {error}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error

    for warning in warnings:
        typer.secho(f"Warning: {warning}", fg=typer.colors.YELLOW, err=True)
    typer.secho(f"Unified schema saved to: {output_path}", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
