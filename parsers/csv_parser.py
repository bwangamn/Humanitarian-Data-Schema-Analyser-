import pandas as pd


class CSVParser:
    """Parser responsible for reading CSV files."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> pd.DataFrame:
        """Read the CSV file and return it as a DataFrame."""

        try:
            df = pd.read_csv(self.file_path)
            return df

        except FileNotFoundError:
            raise FileNotFoundError(
                f"CSV file not found: {self.file_path}"
            )

        except pd.errors.EmptyDataError:
            raise ValueError("The CSV file is empty.")

        except Exception as error:
            raise RuntimeError(
                f"Failed to parse CSV file: {error}"
            )