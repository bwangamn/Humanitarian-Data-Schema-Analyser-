import typer

from parsers.csv_parser import CSVParser
from profiling.profiler import DataProfiler
from schema.schema_builder import SchemaBuilder
from reports.html_report import HTMLReportGenerator


app = typer.Typer()


@app.command()
def analyze(
    file: str,
    output: str = "report.html"
):
    """
    Analyze a humanitarian dataset.
    """

    typer.echo(f"Analyzing: {file}")

    # 1. Parse the CSV
    parser = CSVParser(file)
    df = parser.parse()

    typer.echo(
        f"Loaded {len(df)} rows "
        f"and {len(df.columns)} columns."
    )

    # 2. Profile the data
    profiler = DataProfiler(df)
    profile = profiler.profile()

    # 3. Build schema
    schema_builder = SchemaBuilder(df)
    schema = schema_builder.build()

    # 4. Generate report
    report_generator = HTMLReportGenerator(
        profile,
        schema
    )

    report_generator.generate(output)

    typer.echo(
        f"Analysis complete. Report saved to {output}"
    )


if __name__ == "__main__":
    app()