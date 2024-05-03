# Germinate AI

An experimental framework for building distributed LLM-based multi-agent systems (LLM-MAS). (Using [NATS.io](https://nats.io/))

One tiny step towards a billion agents running a trillion tasks on the cloud, on the edge, on your premises, and on all sorts of IOT devices.

Important: Germinate AI is in the conception, trial and error + initial development stage. A lot of basic features mentioned in the docs aren't implemented yet, or the partial implementations don't actually work!

## Why use Germinate?

Germinate AI lets you define your LLM based systems as a state machine where each state is a tasks DAG. We think that this combination should be flexible and expressive enough to implement a variety of interesting LLM-MAS.

It takes care of scheduling/parallelizing, and storing states/histories during execution.

We use NATS as a message bus enabling ad hoc communication patterns between agents in this distributed swarm of LLM based multi-agents.


## How to get started?

1. Read this page
2. Read the Quickstart
3. Read the MetaGPT-ish (WIP) workflow in `germinate_ai/workflows/metagpt`
4. Skim the reference


### State Machines + DAG specification via an internal DSL

1. Define a workflow which is a State machine
```python
workflow = Workflow(name="create-new-open-source-project")
```

2. Define states and their tasks DAG using an internal DSL for specifying DAGs 

    ```python
    ideate = State(name="ideate")

    @ideate.task(namespace="agents.ideate")
    def brainstorm(...):
        ...

    @ideate.task(namespace="tools.search_github")
    def search_github_for_similar_projects(...):
        ...

    @ideate.task(namespace="agents.ideate")
    def write_pros_and_cons(...):
        ...

    @ideate.task(namespace="agents.ideate")
    def shortlist_ideas(...):
        ...

    # Define tasks DAG via an internal DSL
    (
        brainstorm
        >> [search_github_for_similar_projects, write_pros_and_cons]
        >> shortlist_ideas
    )

    ```

    Germinate seamlessly takes care of scheduling your tasks, executing them in parallel on multiple processes on multiple computers, and storing/passing results to children tasks etc.

3. Define the Workflow's state machine by defining transitions within states using an internal DSL for state machines


    ```python
    @ideate.condition()
    def idea_is_satisfactory(...):
        ...


    # Transition to UI design state from ideate state, if the idea is satisfactory
    (
        (ideate_stage & idea_is_satisfactory)
        >> ui_design_state
    )

    # Transitions are evaluated in order of definition, which can be used to define fallback transitions.

    @ideate.condition()
    def fallback(...):
        return False

    # Transition back to ideate state as a fallback
    (
        (ideate_stage & fallback)
        >> ideate_stage
    )
    ```
    Note: The parentheses in `(<state1> & <condition1>) >> state2` are necessary! 

4. Use DI to inject the dependencies you need in your task definitions. Use langchain, langgraph etc to execute your multi-agent task. Use pydantic models to specify the input and output schemas.

    ```python
    @design_state.task(
        namespace="agent",
    )
    def pm_task(
        input: PMInputSchema,
        chain_factory=Depends(lc_prompt_chain_factory),
    ) -> PMOutputSchema:
        chain = chain_factory(prompt=PRODUCT_MANAGER_PROMPT)

        output_str = chain.invoke(input.product_requirements)
        output_json = extract_json_string(output_str)

        prd_document = PRDDocument.model_validate_json(output_json)
        output = PMOutputSchema(**input.model_dump(), prd_document=prd_document)

        return output
    ```

    ```python
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

    ```


## Project layout
    .
    ├── docker                          # Dockerfiles
    ├── docs                            # Mkdocs Documentation
    ├── germinate_ai                    # Package source files
        |── api                         # REST API
        |── cli
        |── config                      # Configuration
        |── coordinator                 # Coordinates workflow runs
        |── core                        # Common
            |── exceptions
            |── loader                  # Load workflow specs
            |── states                  # State spec
            |── tasks                   # Task spec
            |── workflows               # Workflow spec
        |── data                        # Persistence
            |── database                # Postgres connectors
            |── models                  # SQLAlchemy models
            |── repositories            # SQLAlchemy CRUD
            |── schemas                 # Pydantic schemas
        |── message_bus                 # Message Bus
        |── memory                      # Interfaces and DI factories for Weaviate, NATS KV
        |── toolbox                     # Helpers, and algorithms
        |── utils
        |── worker                      # Task running worker
        |── workflows                   # Runnable Workflow specifications (Temp - see below)
    ├── postgres                        # Postgres configuration
    ├── tests