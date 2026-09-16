import json
import typer
from typing import Optional
from parsers.factory import ParserFactory
from profiling.profiler import DataProfiler
from schema.schema_builder import SchemaBuilder
from reports.html_report import HTMLReportGenerator

app = typer.Typer(
    help="Humanitarian Data Schema Analyser: Unified Schema Profiling and Standardisation CLI."
)


@app.callback()
def main():
    """Analyze humanitarian datasets from the command line."""
    pass


@app.command()
def analyze(
    file: str = typer.Argument(..., help="Path to the dataset file (CSV, JSON, XML, Excel/XLSForm)."),
    output: str = typer.Option("report.html", "--output", "-o", help="Path to save the generated HTML report."),
    schema_output: Optional[str] = typer.Option(None, "--schema-output", "-s", help="Optional path to export the raw JSON Schema file."),
    format: Optional[str] = typer.Option(None, "--format", "-f", help="Explicit format override (csv, json, xml, xlsform).")
):
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


if __name__ == "__main__":
    app()
