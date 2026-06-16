import json
from pathlib import Path
import pandas as pd


class DataLoader:

    @staticmethod
    def load(rules_file):

        with open(rules_file) as f:
            rules = json.load(f)

        datasets = {}

        for parameter, config in rules.items():

            file_stem = config.get("file", parameter)

            for ext, reader in [(".csv", pd.read_csv), (".xlsx", pd.read_excel)]:
                path = Path("data") / f"{file_stem}{ext}"
                if path.exists():
                    datasets[parameter] = reader(path)
                    break
            else:
                raise FileNotFoundError(
                    f"No CSV or XLSX file found for '{parameter}' in data/"
                )

        return datasets