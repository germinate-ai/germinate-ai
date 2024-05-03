from textwrap import dedent
import json

from pydantic import BaseModel
# from loguru import logger

from germinate_ai.core import State
from germinate_ai.utils.di import Depends
from germinate_ai.toolbox.chains import lc_prompt_chain_factory, extract_python_code_string
from germinate_ai.message_bus import ro_message_channel_factory, ROMessageChannel
from germinate_ai.memory.kv import KeyValueStore, kv_story_factory

from .design import PRDDocument, SystemDesignDocument

coding_state = State(name="coding")


# Engineer
# -------------


class EngInputSchema(BaseModel):
    prd_document: PRDDocument
    system_design_document: SystemDesignDocument


class EngOutputSchema(BaseModel):
    code: str


ENGINEER_PROMPT = dedent("""
    You are an expert software engineer.
                         
    Write clean python code implementing the product specified below.

    Product design document:
    ```
    {prd_document}
    ```
                         
    System design document:
    ```
    {system_design_document}
    ```

    Coder team channel messages (if any):
    ```
    {coder_chan_messages}
    ```

    Important: Do not output anything extraneous.
    The output should only include holds the python code you write.
    The python code should be wrapped in ```python and ``` tags.

""")

@coding_state.task(
    namespace="agent"
)
async def eng_task(
    input: EngInputSchema,
    chain_factory=Depends(lc_prompt_chain_factory),
    coders_chan: ROMessageChannel = Depends(ro_message_channel_factory, stream="jobs", subject="jobs.channels.to_coders.>"),
    # kv_store: KeyValueStore = Depends(kv_story_factory, bucket_name="jobs_bucket")
) -> EngOutputSchema:
    chain = chain_factory(prompt=ENGINEER_PROMPT)

    # Debug: read and print kv values
    # votes_so_far = await kv_store.get("votes")
    # if not votes_so_far:
    #     votes_so_far = "{}"
    # votes_so_far = json.loads(votes_so_far)
    # # count votes
    # votes_count = sum(1 for v in votes_so_far.values() if v)
    # print("got votes=", votes_so_far, ", count=", votes_count)

    # read upto 10 messages
    await coders_chan.connect()
    coder_chan_messages =[msg.data for msg in await coders_chan.read(10)]

    vars = dict(**input.model_dump(), coder_chan_messages=coder_chan_messages)

    output_str = chain.invoke(vars)

    code = extract_python_code_string(output_str)

    output = EngOutputSchema(code=code)

    return output