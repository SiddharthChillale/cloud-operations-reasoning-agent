import os

from dotenv import load_dotenv
from smolagents import OpenAIModel

from src.models.constants import API_BASE, MODEL_ID

load_dotenv()

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

openrouter_model = OpenAIModel(
    model_id=MODEL_ID,
    api_base=API_BASE,
    api_key=OPENROUTER_KEY,
)
