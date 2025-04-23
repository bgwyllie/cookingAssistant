import openai

from .config import settings

openai.api_key = settings.OPEN_API_KEY
