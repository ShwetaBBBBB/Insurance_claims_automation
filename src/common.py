import os

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_llm() -> BaseChatModel:
    """
    Returns a base LLM instance based on available environment credentials.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    if not api_key or not azure_endpoint:
        raise ValueError(
            "Missing credentials: Please set OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT."
        )

    return AzureChatOpenAI(
        azure_endpoint=azure_endpoint,
        model_name="gpt-4o",
        temperature=0,
        api_version="2024-08-01-preview",
        openai_api_key=api_key
    )