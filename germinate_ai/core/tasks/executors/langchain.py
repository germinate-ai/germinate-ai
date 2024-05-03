import typing as typ

import attr
from langchain_core.runnables import Runnable as LCRunnable
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from germinate_ai.utils.llms import get_llm

from .base import BaseTaskExecutor


@attr.define(frozen=False)
class LCChainExecutor(BaseTaskExecutor):
    chain: LCRunnable

    def run(self, **kwargs) -> typ.Any:
        output = self.chain.invoke(kwargs)
        return output


@attr.define(init=False, frozen=False)
class LCSimplePromptChainExecutor(LCChainExecutor):
    prompt: PromptTemplate
    llm: BaseChatModel
    output_parser: StrOutputParser

    def __init__(self, prompt: str, llm_code: str):
        self.llm = get_llm(llm_code=llm_code)
        self.prompt = PromptTemplate.from_template(prompt)
        self.output_parser = StrOutputParser()

        self.chain = self.prompt | self.llm | self.output_parser
