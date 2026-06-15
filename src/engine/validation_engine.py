import json
import pandas as pd


class ValidationEngine:

    def __init__(self, datasets, rules_file):

        self.datasets = datasets

        with open(rules_file) as f:
            self.rules = json.load(f)

        self.findings = []

    def validate(self):

        for parameter, config in self.rules.items():

            for rule in config["rules"]:

                rule_type = rule["type"]

                if rule_type == "NOT_NULL":

                    self.validate_not_null(
                        parameter,
                        config,
                        rule
                    )

                elif rule_type == "POSITIVE":

                    self.validate_positive(
                        parameter,
                        config,
                        rule
                    )

                elif rule_type == "EXISTS_IN":

                    self.validate_exists_in(
                        parameter,
                        rule
                    )

                elif rule_type == "ALL_COMBINATIONS_EXIST":

                    self.validate_all_combinations_exist(
                        parameter,
                        config,
                        rule
                    )

        return self.findings

    # =====================================================
    # NOT NULL
    # =====================================================

    def validate_not_null(
            self,
            parameter,
            config,
            rule):

        df = self.datasets[
            config["file"]
        ]

        column = config["column"]

        for _, row in df.iterrows():

            if pd.isna(row[column]):

                finding = {
                    "parameter": parameter,
                    "rule_id": rule["rule_id"],
                    "severity": rule["severity"],
                    "issue": rule["description"]
                }

                finding.update(
                    row.fillna("").to_dict()
                )

                self.findings.append(
                    finding
                )

    # =====================================================
    # POSITIVE
    # =====================================================

    def validate_positive(
            self,
            parameter,
            config,
            rule):

        df = self.datasets[
            config["file"]
        ]

        column = config["column"]

        for _, row in df.iterrows():

            if not pd.isna(row[column]) and row[column] <= 0:

                finding = {
                    "parameter": parameter,
                    "rule_id": rule["rule_id"],
                    "severity": rule["severity"],
                    "issue": rule["description"]
                }

                finding.update(
                    row.fillna("").to_dict()
                )

                self.findings.append(
                    finding
                )

    # =====================================================
    # EXISTS IN
    # =====================================================

    def validate_exists_in(
            self,
            parameter,
            rule):

        source_df = self.datasets[
            rule["source_file"]
        ]

        target_df = self.datasets[
            rule["target_file"]
        ]

        target_values = set(
            target_df[
                rule["target_column"]
            ]
        )

        for _, row in source_df.iterrows():

            value = row[
                rule["source_column"]
            ]

            if value not in target_values:

                finding = {
                    "parameter": parameter,
                    "rule_id": rule["rule_id"],
                    "severity": rule["severity"],
                    "issue": rule["description"]
                }

                finding.update(
                    row.fillna("").to_dict()
                )

                self.findings.append(
                    finding
                )

    # =====================================================
    # ALL COMBINATIONS EXIST
    # =====================================================

    def validate_all_combinations_exist(
            self,
            parameter,
            config,
            rule):

        master_df = self.datasets[
            rule["master_file"]
        ]

        transition_df = self.datasets[
            config["file"]
        ]

        groups = list(
            master_df[
                rule["master_column"]
            ]
        )

        existing_pairs = set(
            zip(
                transition_df[
                    rule["from_column"]
                ],
                transition_df[
                    rule["to_column"]
                ]
            )
        )

        for from_group in groups:

            for to_group in groups:

                if from_group == to_group:
                    continue

                if (
                        from_group,
                        to_group
                ) not in existing_pairs:

                    self.findings.append({

                        "parameter":
                            parameter,

                        "rule_id":
                            rule["rule_id"],

                        "severity":
                            rule["severity"],

                        "issue":
                            rule["description"],

                        "from_group":
                            from_group,

                        "to_group":
                            to_group
                    })