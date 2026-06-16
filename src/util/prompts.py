import yaml
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "resources" / "prompts"

_prompts = {}
for _yml in _PROMPTS_DIR.glob("*.yml"):
    with open(_yml, "r", encoding="utf-8") as _f:
        _prompts.update(yaml.safe_load(_f) or {})


def get_prompt(name):
    return _prompts[name]


# Backwards-compatible module-level names
ai_explainer_prompt = _prompts["ai_explainer_prompt"]
root_cause_prompt = _prompts["root_cause_prompt"]
