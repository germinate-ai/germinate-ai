
from germinate_ai.config import settings

GOOGLE_API_KEY = settings.google_ai_api_key


def get_ollama_llm(llm_code: str):
    """Get an Ollama LLM."""
    from langchain_community.llms import Ollama

    llm = Ollama(model=llm_code)
    return llm


def get_google_llm(llm_code: str):
    """Get Google Generative AI chat model."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(model=llm_code, google_api_key=GOOGLE_API_KEY)
    return llm


DEFAULT_LLM = "google:gemini-pro"

def get_llm(llm_code: str = None):
    """Get an LLM by code.
    
    E.g.
        - "ollama:gemma:7b": "gemma:7b" via Ollama
        - "google:gemini-pro": "gemini-pro" via Google Generative AI
    """
    if llm_code is None:
        llm_code = DEFAULT_LLM
    if llm_code.startswith("ollama:"):
        llm_code = llm_code.replace("ollama:", "")
        return get_ollama_llm(llm_code)
    else:
        # elif llm_code.startswith("google:"):
        llm_code = llm_code.replace("google:", "")
        return get_google_llm(llm_code)
