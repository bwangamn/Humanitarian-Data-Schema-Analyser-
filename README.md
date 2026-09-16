# Humanitarian Data Schema Analyser

This analyser profiles humanitarian CSV datasets and produces a unified JSON schema in an HTML report.

## Setup

Create and activate a virtual environment, then install the project dependencies:

```powershell
python -m venv humanitarian_env
.\humanitarian_env\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run

```powershell
python -m cli.main analyze data/sample.csv --output report.html
```

If the environment is not activated, invoke its interpreter directly:

```powershell
.\humanitarian_env\Scripts\python.exe -m cli.main analyze data/sample.csv --output report.html
```
