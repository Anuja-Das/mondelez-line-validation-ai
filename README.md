# Supply Chain Group Planning — AI Validation Assistant

An agentic data-quality assistant for **Supply Chain Group Planning (GP)** input data.
It validates planner-facing CSVs against business rules and then uses LLM agents to
explain each issue in plain business language and surface the likely root cause.

---

## 1. Problem Statement

Group Planning relies on several interlinked master/transaction files — `Demand`,
`Capacity`, `Group`, `GroupLocation`, `GroupResource`, `Routing`. Before a planning
run, planners must confirm that:

- Mandatory fields (demand qty, capacity, location, resource, routing) are present.
- Quantities/capacities are positive.
- Every demand item belongs to a Group, every Group is mapped to a Location and a
  Resource, and every Resource has a Routing.

Today this review is **manual, repetitive, and error-prone**. When something is
missing, planners also struggle to tell *why* — is it a single bad row, or a wider
master-data gap upstream? A bad input silently produces a bad plan.

## 2. How It Is Solved

A three-stage pipeline turns raw CSVs into a planner-friendly review report:

1. **Data Loading** — all six CSVs are loaded into pandas DataFrames.
2. **Rule-Based Validation** — a configurable JSON rulebook is applied to each
   dataset, producing structured *findings* (parameter, rule, severity, offending
   row).
3. **Agentic AI Analysis** — two LLM agents (Azure OpenAI via LangChain) turn the
   raw findings into business-friendly guidance:
   - **AI Explainer Agent** — explains each finding individually (impact + planner
     action).
   - **Root Cause Correlation Agent** — looks across *all* findings to spot a
     common upstream cause and recommend what to check first.

The result: planners get a prioritized, narrated review instead of a wall of nulls.

---

## 3. What Functional SMEs Can Configure (No Code Changes)

Everything a Planning SME typically wants to tune lives in **config files under
`resources/`** and the **`data/`** folder. No Python edits required.

### 3.1 Validation rules — `resources/validation_rules.json`

The rulebook is data-driven. For each parameter (dataset) you can:

- Add / remove rules.
- Change the **column** being checked.
- Change a rule's **severity** (`High`, `Medium`, `Low`).
- Edit the human-readable **description** (this is what the planner sees).
- Choose a `type` from the supported rule types:
  - `NOT_NULL` — flag missing values in `column`.
  - `POSITIVE` — flag non-positive numeric values in `column`.
  - `ITEM_GROUP_EXISTS` — flag demand items that are not present in `Group`.

Example:

```json
"Demand": {
  "file": "Demand.csv",
  "column": "demand_qty",
  "review_criteria": "Demand quantity should exist for every Item-Location combination",
  "rules": [
    { "rule_id": "D001", "type": "NOT_NULL", "description": "Demand must not be null",   "severity": "High" },
    { "rule_id": "D002", "type": "POSITIVE", "description": "Demand must be greater than zero", "severity": "High" }
  ]
}
```

### 3.2 LLM prompts — `resources/prompts.yml`

The wording used by the AI agents is fully externalized. SMEs can refine tone,
rules, JSON output schema, or word limits **without touching code**:

- `ai_explainer_prompt` — controls the per-finding explanation.
- `root_cause_prompt` — controls the cross-finding root-cause narrative.

Placeholders `{finding}` and `{findings}` are filled in at runtime; the `{{ }}`
blocks are the JSON shape the LLM must return.

### 3.3 Azure OpenAI connection — `resources/application.yml` + `.env`

`application.yml` references environment variables via `${VAR}`. The actual
secrets live in `.env`:

```
API_KEY=<azure-openai-key>
AZURE_ENDPOINT=https://<your-resource>.openai.azure.com/
API_VERSION=2024-xx-xx
```

### 3.4 Input data — `data/*.csv`

Drop the latest planning extracts into `data/` using the same filenames
(`Demand.csv`, `Capacity.csv`, `Group.csv`, `GroupLocation.csv`,
`GroupResource.csv`, `Routing.csv`). No code change needed for a new planning cycle.

---

## 4. Agentic Architecture — End-to-End Flow

```
            ┌──────────────────────────────────────────────────────────────┐
            │                          main.py                              │
            │                       (Orchestrator)                          │
            └───────────────┬──────────────────────────────┬───────────────┘
                            │                              │
                            ▼                              │
        ┌──────────────────────────────┐                   │
        │  DataLoader                  │                   │
        │  src/util/data_loader.py     │                   │
        │                              │                   │
        │  data/*.csv  ─►  dict of     │                   │
        │                  DataFrames  │                   │
        └──────────────┬───────────────┘                   │
                       │                                   │
                       ▼                                   │
        ┌──────────────────────────────┐                   │
        │  ValidationEngine            │                   │
        │  src/engine/                 │                   │
        │     validation_engine.py     │                   │
        │                              │                   │
        │  rules: validation_rules.json│                   │
        │  ─►  list[finding]           │                   │
        └──────────────┬───────────────┘                   │
                       │ findings                          │
                       ├───────────────────────────┐       │
                       ▼                           ▼       ▼
        ┌──────────────────────────────┐   ┌──────────────────────────────┐
        │  AIExplainerAgent            │   │  RootCauseCorrelationAgent   │
        │  src/agents/                 │   │  src/agents/                 │
        │     ai_explainer_agent.py    │   │     root_cause_correlation_  │
        │                              │   │       agent.py               │
        │  per-finding ─► JSON         │   │  all findings ─► JSON        │
        │  {severity, impact_summary,  │   │  {observation, likely_cause, │
        │   planner_action}            │   │   recommended_check}         │
        └──────────────┬───────────────┘   └──────────────┬───────────────┘
                       │                                   │
                       └───────────────┬───────────────────┘
                                       ▼
                          ┌──────────────────────────┐
                          │   Planner-Friendly       │
                          │   Validation Report      │
                          └──────────────────────────┘

  Shared services
  ───────────────
  • src/util/llm_adapter.py   → AzureChatOpenAI client (model: gpt-5.1)
  • src/util/config_loader.py → loads resources/application.yml + .env
  • src/util/prompts.py       → loads resources/prompts.yml (get_prompt(name))
```

**Flow narrative**

1. `main.py` calls `DataLoader.load()` to read the six CSVs.
2. `ValidationEngine(datasets, rules_file)` evaluates `validation_rules.json`
   against the DataFrames and returns a list of structured findings.
3. For **each** finding, `AIExplainerAgent.explain(finding)` invokes the LLM with
   the `ai_explainer_prompt` chain (`PromptTemplate | AzureChatOpenAI`) and
   returns planner-friendly JSON.
4. After the loop, `RootCauseCorrelationAgent.analyze(findings)` sends the full
   set to the LLM with the `root_cause_prompt` chain to identify cross-file
   patterns.
5. All results are printed as a single review report.

Both agents follow the same lightweight LangChain pattern:
`PromptTemplate.from_template(get_prompt(...)) | llm`. New agents can be added
the same way — define a prompt in `prompts.yml`, add a small agent class, plug it
into `main.py`.

---

## 5. How to Run

### Prerequisites
- Python 3.11+
- An Azure OpenAI deployment named **`gpt-5.1`**

### Steps

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure secrets (create .env at project root)
#    API_KEY=...
#    AZURE_ENDPOINT=https://<your-resource>.openai.azure.com/
#    API_VERSION=2024-xx-xx

# 3. (Optional) drop fresh planning CSVs into data/

# 4. (Optional) tweak rules or prompts:
#    - resources/validation_rules.json
#    - resources/prompts.yml

# 5. Run the pipeline
python main.py
```

The console will print, for each finding:

```
Finding: { parameter, rule_id, issue, item, location, resource, severity }
AI Analysis: { severity, impact_summary, planner_action }
```

…followed by a final **Root Cause Analysis** block:

```
{ observation, likely_cause, recommended_check }
```

---

## 6. Project Layout

```
claude-code-tutorial-ai/
├── main.py                          # Pipeline orchestrator
├── requirements.txt
├── data/                            # Input CSVs (SME editable)
│   ├── Demand.csv
│   ├── Capacity.csv
│   ├── Group.csv
│   ├── GroupLocation.csv
│   ├── GroupResource.csv
│   └── Routing.csv
├── resources/                       # Configuration (SME editable)
│   ├── application.yml              # Azure OpenAI config (uses ${ENV})
│   ├── validation_rules.json        # Business validation rulebook
│   └── prompts.yml                  # LLM prompt templates
└── src/
    ├── engine/
    │   └── validation_engine.py     # Rule evaluation
    ├── agents/
    │   ├── ai_explainer_agent.py    # Per-finding explainer
    │   └── root_cause_correlation_agent.py
    └── util/
        ├── data_loader.py
        ├── config_loader.py
        ├── prompts.py               # Loads prompts.yml
        └── llm_adapter.py           # AzureChatOpenAI client
```

