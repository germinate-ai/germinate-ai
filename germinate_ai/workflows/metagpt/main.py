from germinate_ai.core import Workflow

# import states
from .states.design import design_state
from .states.coding import coding_state
# from .states.testing import testing_state, TestsOutputSchema


# Create a workflow
workflow = Workflow(
    name="simple_metagpt",
    version="0.0.1"
)

# Add states to workflow
workflow.add_state(design_state, initial_state=True)
workflow.add_state(coding_state)
# workflow.add_state(testing_state)

# Add transitions to workflow state machine

# First define transition conditions
@design_state.condition()
# TODO input schema
# TODO human review
def design_is_satisfactory(input) -> bool:
    print("running design is satisf")
    print(input)
    return True

@design_state.condition()
# TODO input schema
# TODO human review
def fallback(input) -> bool:
    print("running fallback condition")
    print(input)
    return True



# @Condition.register
# def code_is_executable(input: CodingOutputSchema):
#     # use nc kv to store state TODO
#     return True

# @Condition.register
# def tests_pass(input: TestsOutputSchema):
#     return False


# Transition from design to coding if design is ok
# Note: The parenthesis is necessary!
(design_state & design_is_satisfactory) >> coding_state

# Fallback: restart design
(design_state & fallback) >> design_state


# # Transition from coding to testing if executable
# coding_state & code_is_executable >> testing_state

# # Transition from testing back to coding if tests fail
# testing_state & ~tests_pass >> coding_state

# # Transition to complete if tests pass
# testing_state & tests_pass >> workflow.end