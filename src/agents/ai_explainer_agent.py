import json

from langchain_core.prompts import PromptTemplate

from src.util.llm_adapter import llm
from src.util.prompts import get_prompt


class AIExplainerAgent:

    def explain(self, finding):

        prompt = PromptTemplate.from_template(get_prompt("ai_explainer_prompt"))

        chain = prompt | llm

        response = chain.invoke({
            "finding": json.dumps(
                finding,
                indent=2
            )
        })

        return response.content