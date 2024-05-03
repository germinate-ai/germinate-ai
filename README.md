Germinate AI
=============


Please view the GerminateAI docs: [https://germinate-ai.github.io/germinate-ai/](https://germinate-ai.github.io/germinate-ai/)

## Project Structure

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
        |── memory                      # Agent memory
        |── message_bus                 # Message Bus
        |── toolbox                     # Helpers, and algorithms
        |── utils
        |── worker                      # Task running worker
        |── workflows                   # Runnable Workflow specifications (Temp - see below)
    ├── postgres                        # Postgres configuration
    ├── tests


## Preset Workflows

Preset workflows are temporarily stored in `./germinate_ai/workflows`. This is a temporary until implementation of Docker image builds and the sending pickled task executor functions over the wire.

### MetaGPT-ish (WIP)

WIP

Design state:
Product Manager Task - Writes a simple PRD Document
System Architect Task - Writes a simple System Design Document

Coding state:
Engineer Task - Writes python code in a single generation using only a simple Langchain prompt chain.