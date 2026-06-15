## Problem Statement

Supply chain planning depends on input data from multiple files (demand, capacity, routing, group mappings). When this data contains missing values, invalid numbers, or broken cross-file references, planning outputs become unreliable — and these errors are only discovered after the planning run, causing rework and delays.

**Pain points:**
- No pre-run data quality check across input files
- Errors lack business context — planners don't know what went wrong or why it matters
- Cross-file root causes are invisible without manual analysis

---

## Review Criteria

| Param | Review Criteria |
|-------|-----------------|
| Demand | Demand quantity must be non-null and positive |
| Capacity | Capacity value must be non-null and positive |
| Group | Item referenced in Demand must exist in Group |
| GroupLocation | Group must have a non-null location in GroupLocation |
| GroupResource | Group must be mapped to a non-null resource in GroupResource |
| Routing | Routing ID must be non-null for every routing entry |
| Transition Loss | 1. Default value must be 0.01 (multiplied by 100 in backend to derive actual loss). 2. Higher values must be justified and correctly reflect the expected changeover impact. 3. Transition loss must be defined from each group to every other applicable group — no combinations should be missing. |

---

## Rules

| Rule Type | Description |
|-----------|-------------|
| NOT_NULL | Flags any field that is missing or null |
| POSITIVE | Flags any numeric field whose value is zero or negative |
| EXISTS_IN | Flags any value that does not have a matching entry in a referenced file (referential integrity) |

---

## Extending to a New Parameter — Safety Stock

Suppose the business wants to validate a new parameter. Here's how it works in just 2 steps:

**Step 1: Add the input file** — `data/SafetyStock.csv`

```csv
item,location,safety_stock_qty
OREO_50G,MUMBAI,1000
DAIRYMILK_40G,DELHI,
CADBURY_GEMS,CHENNAI,0
```

**Step 2: Add validation rules** — `resources/validation_rules.json`

```json
"SafetyStock": {
  "file": "SafetyStock",
  "column": "safety_stock_qty",
  "rules": [
    {
      "rule_id": "SS001",
      "type": "NOT_NULL",
      "description": "Safety Stock must not be null",
      "severity": "High"
    },
    {
      "rule_id": "SS002",
      "type": "POSITIVE",
      "description": "Safety Stock must be greater than zero",
      "severity": "High"
    }
  ]
}
```

No code changes required — the pipeline picks up the new parameter automatically.