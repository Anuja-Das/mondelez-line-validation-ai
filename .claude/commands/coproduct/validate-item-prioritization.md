Use the CoProduct Validation Skill.

Execution Mode: Autonomous

Input Files

* input/List of products_Plant_Location_Rates - line 2_New.xlsx
* input/Line_validation_SCRUBBED.xlsx
* input/Fact.ItemPrioritization SCRUBBED.csv

Validation Scope

1. Open List of products_Plant_Location_Rates - line 2_New.xlsx and identify the sheet to read.

2. Extract:

    * Line ← use the sheet name as the Line identifier
    * SKU ← from rows 7–13 within that sheet
    * Type (Mother or Child) ← from rows 7–13 within that sheet

3. Validate Line Exists

    * Line must exist in the Line Validation dataset.

4. Validate CoProduct Enabled

    * Use the Coproduct column to determine if CoProduct is enabled.
    * Only value "Y" means enabled.
    * Any other value means disabled.
    * If disabled, stop validation for that SKU.

5. Validate SKU Exists

    * SKU must exist in the Item Prioritization dataset.

6. Validate Priority Populated

    * Check the MDLZ_Mother Child Item Priority column.
    * Priority value must not be blank, NULL, or missing.

7. Validate Mother Child Priority

    * Group records by Line.
    * Perform validation only within the same Line.
    * Compare every Child SKU against every Mother SKU in that Line.
    * Smaller Priority number means higher Priority.
    * Child Priority number must be lower than Mother Priority number.

Examples

Child = 1
Mother = 2
PASS

Child = 2
Mother = 1
FAIL

General Rules

* Use exact string matching only.
* Do not assume typos.
* Do not perform fuzzy matching.
* Do not infer missing values.
* Do not auto-correct data.
* Missing files are findings.
* Missing columns are findings.
* Continue validation even if some records fail.
* Do not ask questions.
* Do not request clarification.

Output

Return a JSON array followed by a markdown summary table.

Step 1 — JSON Array

Include only FAIL findings. Do not include PASS records.

Each finding must contain:

{
"line":"",
"sku":"",
"type":"",
"validation":"",
"status":"FAIL",
"actual_value":"",
"expected":""
}

Example

[
{
"line":"LINE_B",
"sku":"SKU_1002",
"type":"Mother",
"validation":"Priority Populated",
"status":"FAIL",
"actual_value":"",
"expected":"MDLZ_Mother Child Item Priority must be populated"
}
]

Step 2 — Validation Summary Table

After the JSON array, output a markdown table under the heading:

## Validation Summary

One row per SKU with these columns:

| Line | SKU | Type | Line Exists | CoProduct Enabled | SKU Exists | Priority Populated | Mother Child Priority | Overall |

Column rules:

* Line Exists, CoProduct Enabled, SKU Exists, Priority Populated — show PASS or FAIL.
  Use N/A if the validation was not reached because CoProduct was disabled.
* Mother Child Priority — show PASS if all Child-Mother comparisons for that SKU passed,
  FAIL if any failed, N/A for Mother SKUs or if validation was stopped.
* Overall — FAIL if any column is FAIL, otherwise PASS.
