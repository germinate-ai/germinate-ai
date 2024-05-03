from textwrap import dedent
import typing as typ
import json

from pydantic import BaseModel

from germinate_ai.core import State
from germinate_ai.utils.di import Depends
from germinate_ai.toolbox.chains import lc_prompt_chain_factory, extract_json_string
from germinate_ai.message_bus import wo_message_channel_factory, WOMessageChannel
from germinate_ai.memory.kv import KeyValueStore, kv_story_factory

design_state = State(name="design")


# Product Manager
# ----------------


class PMInputSchema(BaseModel):
    product_requirements: str
    """Product requirements as specified by the client."""


class PRDDocument(BaseModel):
    product_goals: list[str]
    """List of goals of the product/"""

    requirements: list[str]
    """List of requirements."""

    user_stories: list[str]
    """User stories."""


class PMOutputSchema(PMInputSchema):
    prd_document: PRDDocument
    """Product requirement document."""


PRODUCT_MANAGER_PROMPT = dedent("""
    You are an expert product manager.         
    Your job is to create a Product Requirement Document (PRD) from a simple description of the product requirements.
                   
    The document will be handed over to a software architect for the subsequent system design process.

    Please make sure the document is succinct, and describes all the aspects of the product you design thoroughly and clearly.
    The document should be so clear that system designer should be able to create exact designs from this requirements document which 
    will then be used by an engineering team to create a product which matches
    the original requirements exactly.
    
    The document encompasses the goals of the product, user stories, and a requirements list.
    The output should be a JSON string with the keys "product_goals" (a list of strings), "user_stories" (a list of strings) and "requirements" (a list of strings).

    Important: Do not output anything extraneous. The output should include only the correctly formatted JSON string and nothing else.
    Make sure to wrap the answer in ```json and ``` tags

    The original product description is:
    {product_requirements}

""")
# Output your answer as JSON that matches the given schema: ```json\n{output_schema}\n```.


# if multiple depends on, combined inputs
@design_state.task(
    namespace="agent",
)
# Auto validates schemas
# Fills in nc and db dependencies if asked for
def pm_task(
    input: PMInputSchema,
    chain_factory=Depends(lc_prompt_chain_factory),
) -> PMOutputSchema:
    chain = chain_factory(prompt=PRODUCT_MANAGER_PROMPT)

    output_str = chain.invoke(input.product_requirements)

    print("design task output")
    from pprint import pprint
    pprint(output_str)

    output_json = extract_json_string(output_str)

    prd_document = PRDDocument.model_validate_json(output_json)
    output = PMOutputSchema(**input.model_dump(), prd_document=prd_document)

    return output


# System Architect
# ----------------


class SAInputSchema(BaseModel):
    prd_document: PRDDocument
    """Product requirement document."""


class SystemDesignDocument(BaseModel):
    implementation_approach: str
    """"""

    python_package_name: str
    """Name of python package."""

    python_files: list[str]
    """List of python files to create."""

    coders_messages: typ.Optional[str] = ""



class SAOutputSchema(SAInputSchema):
    prd_document: PRDDocument
    """Product requirement document."""

    system_design_document: SystemDesignDocument
    """System design document."""


SYSTEM_ARCHITECT_PROMPT = dedent("""
    You are an expert systems architect.
    Your job is to create technical specifications from a Product Design Document written by the product manager based on the client's requirements.
    
    Consider the the overarching technical trajectory while writing the document.
    Define the project's architecture (including the file names and project structure), classes and sequence flow.
                          
    The document will be handed over to the engineering team for task allocation and implementation based on your exact specifications.
    Please make sure the document is succinct, and describes all the aspects of the product you design thoroughly and succinctly.
    The document should be so clear that they can be used by engineering team to create a product which matches the requirements exactly.
    If there is anything you need to fulfill your job that is unclear in the specifications given to you, you can list what you need in an "Unclear Points" section.

    The sections in the system design document should be
    - Implementation Approach (a single string under the JSON key "implementation_approach")
    - Python package name (a single string under the JSON key "python_package_name")
    - Python file list (a list of strings under the JSON key "python_files")
    - Any extra instructions for the coders (a single string under the JSON key "coders_messages") e.g. conventions and guidelines to follow.
                                 
    The output should be a JSON string with the keys "implementation_approach", "python_package_name" and "python_files".

    Important: Do not output anything extraneous. The output should include only the correctly formatted JSON string and nothing else.
    Make sure to wrap the answer in ```json and ``` tags

    The product design document is:
    ```
    {prd_document}
    ```
""")


@design_state.task(
    namespace="agent",
)
async def sa_task(
    input: SAInputSchema,
    chain_factory=Depends(lc_prompt_chain_factory),
    coders_chan: WOMessageChannel =Depends(wo_message_channel_factory, stream="jobs", subject="jobs.channels.to_coders.from_sa"),
    kv_store: KeyValueStore = Depends(kv_story_factory, bucket_name="jobs_bucket")
) -> SAOutputSchema:
    chain = chain_factory(prompt=SYSTEM_ARCHITECT_PROMPT)

    output_str = chain.invoke(input.prd_document)

    print("sa task output")
    from pprint import pprint
    pprint(output_str)


    output_json = extract_json_string(output_str)

    system_design_document = SystemDesignDocument.model_validate_json(output_json)
    output = SAOutputSchema(
        **input.model_dump(), system_design_document=system_design_document
    )

    # Debug add fake messages
    system_design_document.coders_messages = "SA: Follow all the python best practices and conventions."

    # write extra messages for coders into chan
    if system_design_document.coders_messages:
        await coders_chan.connect()
        await coders_chan.write(system_design_document.coders_messages)

    # Debug store fake value in kv store
    await kv_store.connect()
    votes_so_far = {}
    votes_so_far["sa"] = True
    await kv_store.put("votes", json.dumps(votes_so_far))

    return output


# Define dependencies
# design_state.start >> pm_task >> sa_task >> design_state.end
pm_task >> sa_task
