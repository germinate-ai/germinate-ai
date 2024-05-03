import re
import typing as typ

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable as LCRunnable

from germinate_ai.utils.llms import get_llm as _get_llm


def lc_prompt_chain_factory(
    llm_code: str = None,
    get_llm: typ.Callable[[], BaseChatModel] = None,
) -> LCRunnable:
    """Create a simple Langchain prompt chain from the prompt, and LLM (specified via a code or a getter function.)"""
    if get_llm:
        llm = get_llm()
    else:
        llm = _get_llm(llm_code=llm_code)

    def factory(prompt: str):
        prompt = PromptTemplate.from_template(prompt)
        output_parser = StrOutputParser()
        chain = prompt | llm | output_parser

        return chain

    return factory


def extract_tagged_strings(text: str, tagname: str) -> typ.List[str]:
    """Extracts strings from a string where the relevant is embedded between ```<tagname> and ``` tags.

    Parameters:
        text (str): The text containing the relevant content.

    Returns:
        list: A list of extracted relevant strings.
    """
    pattern = r"```" + tagname + r"(.*?)```"

    matches = re.findall(pattern, text, re.DOTALL)
    return [m.strip() for m in matches]

# JSON strings

def extract_json_strings(text: str) -> typ.List[str]:
    """Extracts JSON strings from a string where JSON is embedded between ```json and ``` tags.

    Parameters:
        text (str): The text containing the JSON content.

    Returns:
        list: A list of extracted JSON strings.
    """
    return extract_tagged_strings(text, r"json")



def extract_json_string(text: str) -> typ.List[str]:
    """Extracts the first JSON string from a string where JSON is embedded between ```json and ``` tags.

    Parameters:
        text (str): The text containing the JSON content.

    Returns:
        str: The extracted JSON string.
    """
    json_strs = extract_json_strings(text)
    if len(json_strs) > 0:
        return json_strs[0]
    else:
        raise ValueError(
            "Invalid input text: Text does not contain JSON strings between ```json and ``` tags"
        )
    


# Python code

def extract_python_code_strings(text: str) -> typ.List[str]:
    """Extracts python code strings from a string where they are is embedded between ```python and ``` tags.

    Parameters:
        text (str): The text containing the python code.

    Returns:
        list: A list of extracted code.
    """
    return extract_tagged_strings(text, r"python")


def extract_python_code_string(text: str) -> typ.List[str]:
    """Extracts python code strings from a string where they are is embedded between ```python and ``` tags.

    Parameters:
        text (str): The text containing the python code.

    Returns:
        list: A list of extracted code.
    """
    json_strs = extract_python_code_strings(text)
    if len(json_strs) > 0:
        return json_strs[0]
    else:
        raise ValueError(
            "Invalid input text: Text does not contain python code between ```python and ``` tags"
        )