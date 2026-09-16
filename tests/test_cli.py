from typer.testing import CliRunner
from cli.main import app

runner = CliRunner()


def test_cli_analyze_csv(tmp_path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("id,val\n1,10\n2,20\n")

    output_html = tmp_path / "report.html"
    output_schema = tmp_path / "schema.json"

    result = runner.invoke(app, [
        "analyze", str(csv_file),
        "--output", str(output_html),
        "--schema-output", str(output_schema)
    ])

    assert result.exit_code == 0
    assert "Analysis complete!" in result.stdout
    assert output_html.exists()
    assert output_schema.exists()
