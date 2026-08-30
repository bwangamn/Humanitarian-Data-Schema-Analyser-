import pandas as pd


class DataProfiler:
    """Analyzes the quality and characteristics of a dataset."""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def profile(self) -> dict:
        """Generate a basic profile of the dataset."""

        profile = {
            "row_count": len(self.df),
            "column_count": len(self.df.columns),
            "columns": {}
        }

        for column in self.df.columns:

            series = self.df[column]

            profile["columns"][column] = {
                "data_type": str(series.dtype),
                "missing_values": int(series.isna().sum()),
                "missing_percentage": round(
                    series.isna().mean() * 100,
                    2
                ),
                "unique_values": int(series.nunique())
            }

        return profile