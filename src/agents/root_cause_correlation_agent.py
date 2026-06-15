import json

from langchain_core.prompts import PromptTemplate

from src.util.prompts import get_prompt
from src.util.llm_adapter import llm


class RootCauseCorrelationAgent:

    def analyze(self, findings):

        prompt = PromptTemplate.from_template(
            get_prompt("root_cause_prompt")
        )

        chain = prompt | llm

        findings_json = json.dumps(
            findings,
            indent=2
        )

        response = chain.invoke({
            "findings": findings_json
        })

        return response.content