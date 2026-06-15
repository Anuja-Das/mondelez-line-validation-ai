import json
import pandas as pd


class DataLoader:

    @staticmethod
    def load(rules_file):

        with open(rules_file) as f:
            rules = json.load(f)

        datasets = {}

        for parameter, config in rules.items():

            file_stem = config.get("file", parameter)

            datasets[parameter] = pd.read_csv(
                f"data/{file_stem}.csv"
            )

        return datasets