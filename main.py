from src.util.data_loader import DataLoader
from src.engine.validation_engine import ValidationEngine
from src.agents.ai_explainer_agent import AIExplainerAgent
from src.agents.root_cause_correlation_agent import RootCauseCorrelationAgent


RULES_FILE = "resources/validation_rules.json"

datasets = DataLoader.load(RULES_FILE)

engine = ValidationEngine(
    datasets=datasets,
    rules_file=RULES_FILE
)

explainer = AIExplainerAgent()

findings = engine.validate()

print("\nVALIDATION REPORT")
print("=" * 80)

for finding in findings:

    print("\nFinding:")
    print(finding)

    explanation = explainer.explain(
        finding
    )

    print("\nAI Analysis:")
    print(explanation)

    print("=" * 80)

root_cause_agent = RootCauseCorrelationAgent()

correlation_result = root_cause_agent.analyze(
    findings
)

print("\nROOT CAUSE ANALYSIS")
print("=" * 80)

print(correlation_result)