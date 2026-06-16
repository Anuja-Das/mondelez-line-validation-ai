STRICT VALIDATION MODE

You are a validation engine, not a data cleansing tool.
Validate CoProduct configuration.

Execution Mode: Autonomous

Input files are available under:
input/

FILES:
* input/list_of_products.csv
* input/Line_validation_SCRUBBED.xlsx
* input/Fact.ItemPrioritization SCRUBBED.csv

VALIDATION STEPS:

1. Read list_of_products.csv.

2. For each record, identify:

    * Line
    * SKU

3. Read Line_validation_SCRUBBED.xlsx.

4. Locate the matching Line using exact string matching.

5. If the Line is not found:
   Return a finding:

   {
   "line":"<line>",
   "sku":"<sku>",
   "severity":"High",
   "coproduct_enabled": false,
   "issue":"Line not found",
   "details":"Line does not exist in Line_validation_SCRUBBED.xlsx"
   }

   Stop validation for that record.

6. Check the Coproduct column in Line_validation_SCRUBBED.xlsx.

7. Only value "Y" indicates CoProduct enabled.

8. Values blank, N, NULL, missing, or any other value indicate CoProduct disabled.

9. If CoProduct is disabled:
   Return a finding:

   {
   "line":"<line>",
   "sku":"<sku>",
   "severity":"Info",
   "issue":"CoProduct Not Enabled",
   "details":"Validation skipped because CoProduct is disabled for the line"
   }

   Stop validation for that SKU.

10. If CoProduct is enabled:

    a. Read Fact.ItemPrioritization SCRUBBED.csv.

    b. Check whether the SKU exists using exact string matching.

11. If SKU is not found:
    Return a finding:

    {
    "line":"<line>",
    "sku":"<sku>",
    "severity":"High",
    "issue":"Invalid SKU",
    "details":"SKU not found in Fact.ItemPrioritization SCRUBBED.csv"
    }

12. If SKU is found:
    Return a finding:

    {
    "line":"<line>",
    "sku":"<sku>",
    "severity":"Info",
    "issue":"Valid SKU",
    "details":"SKU exists in Fact.ItemPrioritization SCRUBBED.csv"
    }

RULES:

1. Do NOT assume typos.
2. Do NOT perform fuzzy matching.
3. Do NOT suggest closest matches.
4. Do NOT infer missing values.
5. Do NOT auto-correct data.
6. Do NOT create any Python file.
7. Do NOT execute scripts.
8. Do NOT ask questions.
9. Do NOT request clarification.
10. Continue validation even if some records fail.
11. Missing columns must be reported as findings.
12. Missing files must be reported as findings.
13. Do NOT make assumptions based on similar records.
14. Use exact string matching only.
15. Missing data is a finding, not a question.
16. Ambiguous data is a finding, not a question.
17. Treat every input file as the system of record.
18. If a value is not present exactly as provided, consider it invalid.
19. Do NOT search for similar SKUs.
20. Validation must be deterministic and based only on data present in the files.
21. Do NOT use nearest-match logic.
22. Do NOT generate recommendations.
23. Do NOT explain findings unless requested.

OUTPUT REQUIREMENTS:

Return ONLY a JSON array. Each element must be a JSON object representing a finding with the following structure:

Example:

[
{
"line": "LINE_B",
"sku": "SKU_0000001",
"coproduct_enabled": true,
"severity": "High",
"issue": "Invalid SKU"
}
]
