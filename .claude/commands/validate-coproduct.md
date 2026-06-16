Use the CoProduct Validation Skill.

Execution Mode: Autonomous

Input Files

* input/List of products_Plant_Location_Rates - line 2_New.xlsx
* input/Line_validation_SCRUBBED.xlsx
* input/Fact.ItemPrioritization SCRUBBED.csv

Validation Scope

1. Read Rows 7-13 from List of products_Plant_Location_Rates - line 2_New.xlsx.

2. Extract:

    * Line
    * SKU
    * Type (Mother or Child)

3. Validate Line Exists

    * Line must exist in Line_validation_SCRUBBED.xlsx.

4. Validate CoProduct Enabled

    * Use Coproduct column from Line_validation_SCRUBBED.xlsx.
    * Only value "Y" means enabled.
    * Any other value means disabled.
    * If disabled, stop validation for that SKU.

5. Validate SKU Exists

    * SKU must exist in Fact.ItemPrioritization SCRUBBED.csv.

6. Validate Priority Populated

    * Priority value is mentioned in MDLZ_Mother Child Item Priority column in Fact.ItemPrioritization SCRUBBED.csv.
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

Return ONLY a JSON array.

Each finding must contain:

{
"line":"",
"sku":"",
"type":"",
"validation":"",
"status":"PASS|FAIL",
"actual_value":"",
"expected":""
}

Example

[
{
"line":"LINE_B",
"sku":"SKU_1001",
"type":"Child",
"validation":"SKU Exists",
"status":"PASS",
"actual_value":"SKU_1001",
"expected":"SKU must exist in Item Prioritization"
},
{
"line":"LINE_B",
"sku":"SKU_1002",
"type":"Mother",
"validation":"Priority Populated",
"status":"FAIL",
"actual_value":"",
"expected":"Priority must be populated"
}
]
