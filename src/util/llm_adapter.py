from langchain_openai import AzureChatOpenAI
from src.util.config_loader import config

llm = AzureChatOpenAI(
    api_key=config.get("api_key"),
    azure_endpoint=config.get("azure_endpoint"),
    api_version=config.get("api_version"),
    azure_deployment=config.get("ai_model")
)

def call_llm(messages):
    response = llm.chat.completions.create(
        model="gpt-5.1",
        messages=messages,
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content