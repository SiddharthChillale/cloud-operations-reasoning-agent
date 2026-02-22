import os

from dotenv import load_dotenv
from smolagents import OpenAIModel

load_dotenv()

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

openrouter_model = OpenAIModel(
    model_id="qwen/qwen3-coder",
    api_base="https://openrouter.ai/api/v1/",
    api_key=OPENROUTER_KEY,
)
