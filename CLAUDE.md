# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Mondelez Supply Chain Group Planning — AI Validation Assistant** is an agentic data-quality system that validates planning input CSVs and uses Azure OpenAI LLM agents to explain issues and identify root causes in plain business language. It reduces manual review and helps planners understand *why* data is invalid.

### Core Problem

Supply chain planners must manually validate six interlinked master/transaction files before planning runs. Data errors (missing fields, invalid quantities, broken references) go undetected until planning execution, causing rework. Issues lack business context — planners don't know what went wrong or why it matters.

### How It Works (Three-Stage Pipeline)

1. **Data Loading** (`src/util/data_loader.py`) — Reads CSV files into pandas DataFrames based on rules config.
2. **Rule-Based Validation** (`src/engine/validation_engine.py`) — Applies configurable JSON rulebook to each dataset, producing structured findings (parameter, rule_id, severity, offending row).
3. **Agentic AI Analysis** — Two LLM agents turn raw findings into business-friendly guidance:
   - `AIExplainerAgent` — Explains each finding individually (impact + planner action)
   - `RootCauseCorrelationAgent` — Identifies cross-file patterns and recommends what to check first

**Result**: Planners get a prioritized, narrated review instead of raw nulls/errors.

## Architecture & Key Design Decisions

### Three-File Configuration Model (SME-Editable, No Code Changes)

Everything a Planning SME tunes lives in `resources/` and `data/`:

- **`resources/validation_rules.json`** — Data-driven rulebook defining what to check per parameter (Demand, Capacity, Group, GroupLocation, GroupResource, Routing, TransitionLoss). Supports rule types:
  - `NOT_NULL` — Flag missing values in a column
  - `POSITIVE` — Flag non-positive numeric values
  - `EXISTS_IN` — Flag values not present in a reference file (referential integrity)
  - `ALL_COMBINATIONS_EXIST` — Verify all pairwise combinations exist (e.g., transition loss between all group pairs)

- **`resources/prompts.yml`** — LLM prompt templates for both agents, including JSON output schema. SMEs refine tone/rules without touching code.

- **`resources/application.yml`** — Azure OpenAI connection config (references env vars via `${VAR}` syntax); actual secrets in `.env`.

### LangChain Chain Pattern

Both agents follow the same lightweight pattern:
```python
chain = PromptTemplate.from_template(get_prompt(name)) | llm
response = chain.invoke({...})
```

This makes it trivial to add new agents — define a prompt in `prompts.yml`, create a small agent class, plug it into `main.py`.

### Orchestrator Flow (`main.py`)

1. `DataLoader.load(RULES_FILE)` reads all CSVs → dict of DataFrames
2. `ValidationEngine(datasets, rules_file).validate()` evaluates rules → list of findings
3. Loop: `AIExplainerAgent.explain(finding)` for each finding → LLM JSON response
4. `RootCauseCorrelationAgent.analyze(findings)` → Cross-finding pattern JSON
5. Print planner-friendly report

## Common Commands

### Setup & Prerequisites

```powershell
# 1. Ensure Python 3.11+ is installed
python --version

# 2. Create virtual environment (if not already done)
python -m venv .venv

# 3. Activate virtual environment
.venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure secrets (.env at project root)
# Create .env with:
#   API_KEY=<azure-openai-key>
#   AZURE_ENDPOINT=https://<your-resource>.openai.azure.com/
#   API_VERSION=2024-xx-xx
#   AI_MODEL=gpt-5.1
```

### Run the Pipeline

```powershell
# Activate venv first
.venv\Scripts\activate

# Run validation and AI analysis
python main.py
```

The console prints:
- Per-finding validation issues + AI explanations (JSON: severity, impact_summary, planner_action)
- Final Root Cause Analysis block (JSON: observation, likely_cause, recommended_check)

### Modifying Validation Rules (No Code Changes)

Edit `resources/validation_rules.json` to:
- Add/remove rules
- Change severity (High, Medium, Low)
- Edit human-readable descriptions (what planners see)
- Support new parameters by adding them with a matching CSV in `data/`

Example adding a new parameter `SafetyStock`:
1. Drop `data/SafetyStock.csv`
2. Add to `validation_rules.json`:
```json
"SafetyStock": {
  "file": "SafetyStock",
  "column": "safety_stock_qty",
  "rules": [
    {"rule_id": "SS001", "type": "NOT_NULL", "description": "Safety Stock must not be null", "severity": "High"}
  ]
}
```
Pipeline auto-picks it up — no code changes needed.

### Modifying LLM Prompts (No Code Changes)

Edit `resources/prompts.yml` to refine:
- Tone and wording for AI explanations
- JSON output schema (severity values, field names)
- Word limits and business language rules
- Rule interpretations for the agents

Both `ai_explainer_prompt` and `root_cause_prompt` use placeholders:
- `{finding}` / `{findings}` filled in at runtime
- `{{ }}` blocks define the JSON shape the LLM must return

### Extending Input Data

Drop new planning CSVs into `data/` using the configured filenames. Pipeline loads them automatically on next run.

## Module & File Structure (For Developers)

### Key Files

| File | Purpose |
|------|---------|
| `main.py` | Orchestrator — calls DataLoader → ValidationEngine → both agents |
| `src/util/data_loader.py` | Reads CSVs into pandas DataFrames based on rules config |
| `src/engine/validation_engine.py` | Evaluates all rule types (NOT_NULL, POSITIVE, EXISTS_IN, ALL_COMBINATIONS_EXIST) |
| `src/agents/ai_explainer_agent.py` | LLM chain that explains a single finding |
| `src/agents/root_cause_correlation_agent.py` | LLM chain that identifies cross-finding patterns |
| `src/util/llm_adapter.py` | AzureChatOpenAI client initialization |
| `src/util/config_loader.py` | Loads `application.yml` and interpolates env vars from `.env` |
| `src/util/prompts.py` | Loads `resources/prompts.yml` (get_prompt(name)) |

### Data Files

- `data/*.csv` — Input datasets for validation (Demand, Capacity, Group, GroupLocation, GroupResource, Routing, TransitionLoss, etc.)
- `input/` — External reference files (GP validation points, scrubbed line validation data)

## Adding a New Validation Rule Type

To support a new rule type beyond `NOT_NULL`, `POSITIVE`, `EXISTS_IN`, `ALL_COMBINATIONS_EXIST`:

1. Add a new method to `ValidationEngine`:
```python
def validate_custom_rule(self, parameter, config, rule):
    df = self.datasets[config["file"]]
    # Logic here; append to self.findings
```

2. Add a handler in `ValidationEngine.validate()`:
```python
elif rule_type == "CUSTOM_RULE":
    self.validate_custom_rule(parameter, config, rule)
```

3. Document the rule type in `resources/validation_rules.json` examples.

## Adding a New LLM Agent

To add a new agent (e.g., data profiler, trend analyzer):

1. Create `src/agents/your_agent.py`:
```python
from langchain_core.prompts import PromptTemplate
from src.util.llm_adapter import llm
from src.util.prompts import get_prompt

class YourAgent:
    def analyze(self, findings):
        chain = PromptTemplate.from_template(get_prompt("your_prompt")) | llm
        response = chain.invoke({"findings": json.dumps(findings, indent=2)})
        return response.content
```

2. Add prompt to `resources/prompts.yml`:
```yaml
your_prompt: |
  Your prompt template here
  {findings}
  ...
```

3. Import and call in `main.py`.

## Common Issues & Troubleshooting

### "Module not found" errors
- Ensure `.venv` is activated: `.venv\Scripts\activate`
- Verify `pip install -r requirements.txt` completed

### Azure OpenAI connection fails
- Check `.env` has all four vars: `API_KEY`, `AZURE_ENDPOINT`, `API_VERSION`, `AI_MODEL`
- Verify Azure resource exists and deployment name matches `ai_model` in `.env`

### CSV file not found
- Check `data/` folder has all required CSVs matching filenames in `validation_rules.json`
- Ensure column names in CSV headers match `config["column"]` in rules

### LLM returns invalid JSON
- Review prompts in `resources/prompts.yml` — ensure `{{ }}` blocks are clear and valid JSON schema
- Check finding/findings are properly serialized as JSON strings before passing to LLM

## Dependencies

- **openai** — Azure OpenAI SDK
- **pandas** — DataFrame manipulation
- **langchain** — Core agent/chain framework
- **langchain-openai** — Azure OpenAI integration
- **python-dotenv** — Environment variable loading from `.env`

See `requirements.txt` for pinned versions.

## Design Principles

1. **Configuration Over Code** — SMEs tune rules, prompts, and data without touching Python
2. **Lightweight Agent Pattern** — LangChain chains (`PromptTemplate | LLM`) keep agent code minimal
3. **Structured Findings** — Each validation issue is a dict with parameter, rule_id, severity, and row data
4. **Business Language** — Prompts enforce simple, planner-focused explanations (no technical jargon)
5. **Extensibility** — New rule types, agents, and parameters follow the same patterns
