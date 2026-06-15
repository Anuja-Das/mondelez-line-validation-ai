import yaml
from pathlib import Path

PROMPTS_PATH = Path(__file__).resolve().parents[2] / "resources" / "prompts.yml"

with open(PROMPTS_PATH, "r", encoding="utf-8") as _f:
    _prompts = yaml.safe_load(_f) or {}


def get_prompt(name):
    return _prompts[name]


# Backwards-compatible module-level names
ai_explainer_prompt = _prompts["ai_explainer_prompt"]
root_cause_prompt = _prompts["root_cause_prompt"]
