"""Tests that the HTML report escapes values taken from the input data."""

from typer.testing import CliRunner

from humanitarian_schema_analyzer.cli.main import app

runner = CliRunner()


def test_html_report_escapes_html_like_input(tmp_path):
    csv_file = tmp_path / "hostile.csv"
    csv_file.write_text(
        '<img src=x onerror=alert(1)>,note\n<script>alert(1)</script>,a&b\n',
        encoding="utf-8",
    )
    report = tmp_path / "report.html"
    schema = tmp_path / "schema.json"

    result = runner.invoke(
        app, ["analyze", str(csv_file), "--output", str(report), "--schema-output", str(schema)]
    )

    assert result.exit_code == 0, result.output
    page = report.read_text(encoding="utf-8")
    assert "<img src=x onerror" not in page
    assert "<script>alert(1)</script>" not in page
    assert "&lt;img src=x onerror=alert(1)&gt;" in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert "a&amp;b" in page
