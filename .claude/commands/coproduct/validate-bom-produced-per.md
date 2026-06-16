Use the BOM Produced Per Validation Skill.

Execution Mode: Autonomous

## Input Files

* `input/List of products_Plant_Location_Rates - line 2_New.xlsx`
* `input/Fact.BOM Quantity Produced Per SCRUBBED.csv`

---

## Step 1 — Extract Slug SKUs from Product List

1. Open the Excel file and read the first sheet (sheet name = the line identifier, e.g., `LINE_B`).
2. Read all rows without a header — treat every row by its raw index (0-based).
3. Scan rows 6 through 14 (inclusive) to find the product list section.
4. Column index 5 contains the Type value. Identify rows where column 5 = `"Child"`.
5. Column index 3 contains the SKU. Extract the SKU value from those rows.
6. These extracted SKUs are the **slug SKUs** to validate.

---

## Step 2 — Validation 1: Co-Product Must Exist in Slug SKU BOM

Load the BOM CSV (`Fact.BOM Quantity Produced Per SCRUBBED.csv`).

For each slug SKU extracted in Step 1:

**2a. Find co-product BOM rows**

Search for rows in the BOM CSV where:
- `Activity1.[Activity1]` contains the slug SKU identifier
  (e.g., for `SKU_00324`, match rows where Activity1 = `BOM_01_LOC001_SKU_00324` or any variant that embeds the same SKU ID)
- AND `Item.[Item]` starts with `GROUP`

These are the **co-product rows** for the slug SKU.

**2b. Check co-product exists**

If no co-product rows are found:
- Record a FAIL finding:
  - `validation`: `"Co-Product in BOM"`
  - `actual_value`: `"No GROUP item found in BOM for this slug SKU"`
  - `expected`: `"At least one GROUP item must exist in the slug SKU's BOM"`
- Mark this slug SKU as INVALID. Skip Step 3 for it.

**2c. Check o9 BOM Association**

For each co-product row found:
- If `o9 BOM Association` is null, blank, or missing:
  - FAIL: `validation` = `"o9 BOM Association"`, `actual_value` = `""`, `expected` = `"o9 BOM Association must be populated"`
- If `o9 BOM Association` ≠ 1:
  - FAIL: `validation` = `"o9 BOM Association"`, `actual_value` = the actual value, `expected` = `"o9 BOM Association must equal 1"`

**2d. Check o9 BOM Quantity Produced Per**

For each co-product row found:
- If `o9 BOM Quantity Produced Per` is null, blank, or missing:
  - FAIL: `validation` = `"o9 BOM Quantity Produced Per"`, `actual_value` = `""`, `expected` = `"o9 BOM Quantity Produced Per must be populated"`
- If `o9 BOM Quantity Produced Per` ≤ 0:
  - FAIL: `validation` = `"o9 BOM Quantity Produced Per"`, `actual_value` = the actual value, `expected` = `"o9 BOM Quantity Produced Per must be a positive value"`

A slug SKU is **VALID** from Validation 1 only if all checks in 2b, 2c, and 2d pass.

---

## Step 3 — Validation 2: BOM Ratio Must Match Defined Rate

Only perform this step for slug SKUs that are **VALID** from Step 2.

**3a. Get BOM Quantity Produced Per**

From the co-product row found in Step 2, read the value of `o9 BOM Quantity Produced Per`.

**3b. Find the Scenario 2 table in the Excel file**

In the Excel file, scan rows beyond the product list section to find the Scenario 2 production table:
- Look for a row where a cell contains text like `"Scenario 2"` or `"Production Multipack & Slug"`.
- The header row for that table contains `"Productivity Kg/shift"` in column index 5.
- The data rows immediately below that header will have:
  - A row where column index 2 (Format) = `"MULTIPACK"` (or Details column contains `"MULTIPACK"`)
  - A row where column index 2 (Format) = `"SLUG"` (or Details column contains `"SLUG"`)
- Do **not** use any table found under a row labelled `"internal calculation"`.
- If multiple Scenario 2 tables exist for different flavors, identify which flavor group the slug SKU belongs to (from the product list, column index 1 of the same flavor block), and use the Scenario 2 table that corresponds to the same flavor.

**3c. Calculate the expected ratio**

```
ratio = MULTIPACK Productivity Kg/shift ÷ SLUG Productivity Kg/shift
expected_ratio = truncate(ratio, 2)  — take the raw value as-is to 2 decimal places; do NOT round
```

To truncate to 2 decimal places without rounding: `int(ratio * 100) / 100`

**3d. Compare**

```
actual_value = truncate(o9 BOM Quantity Produced Per, 2)  — take the raw value as-is to 2 decimal places; do NOT round
```

To truncate to 2 decimal places without rounding: `int(value * 100) / 100`

If `actual_value` ≠ `expected_ratio`:
- FAIL:
  - `validation`: `"BOM Ratio Match"`
  - `actual_value`: the actual BOM value (truncated to 2 decimal places, not rounded)
  - `expected`: `"o9 BOM Quantity Produced Per should be {expected_ratio} (Multipack {multipack_val} ÷ Slug {slug_val})"`

---

## General Rules

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
* **Do not round off any numeric value.** All numeric values must be taken as-is, truncated to 2 decimal places. Use truncation (`int(value * 100) / 100`), never `round()`.

---

## Output

Return a JSON array followed by a markdown summary table.

### Step 1 — JSON Array

Include only FAIL findings. Do not include PASS records.

Each finding must contain:

```json
{
  "slug_sku": "",
  "validation": "",
  "status": "FAIL",
  "actual_value": "",
  "expected": ""
}
```

Example:

```json
[
  {
    "slug_sku": "SKU_00324",
    "validation": "BOM Ratio Match",
    "status": "FAIL",
    "actual_value": "1.00",
    "expected": "o9 BOM Quantity Produced Per should be 4.55 (Multipack 4184.89 ÷ Slug 918.63)"
  }
]
```

### Step 2 — Validation Summary Table

After the JSON array, output a markdown table under the heading:

## Validation Summary

One row per slug SKU with these columns:

| Slug SKU | Co-Product in BOM | o9 BOM Association | o9 BOM Qty Produced Per | BOM Ratio Match | Expected Ratio | Actual BOM Value | Overall |

Column rules:

* Co-Product in BOM — PASS or FAIL.
* o9 BOM Association — PASS or FAIL. Use N/A if Co-Product in BOM is FAIL.
* o9 BOM Qty Produced Per — PASS or FAIL. Use N/A if Co-Product in BOM is FAIL.
* BOM Ratio Match — PASS or FAIL. Use N/A if any Validation 1 check failed.
* Expected Ratio — the calculated ratio truncated to 2 decimal places (not rounded), or N/A if not reached.
* Actual BOM Value — the o9 BOM Quantity Produced Per truncated to 2 decimal places (not rounded), or N/A if not reached.
* Overall — FAIL if any column is FAIL, otherwise PASS.
