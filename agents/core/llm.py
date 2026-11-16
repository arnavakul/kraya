
from groq import Groq

from core.config import settings


def get_llm_client() -> Groq:
    """
    Creates and returns a Groq LLM client.
    """

    client = Groq(
        api_key=settings.GROQ_API_KEY.get_secret_value()
    )

    return client

'''
What does get_llm_client() do?
1. Retrieves our API key from configuration.
2. Initializes the Groq client.
3. Returns the client so other components can use it.
'''