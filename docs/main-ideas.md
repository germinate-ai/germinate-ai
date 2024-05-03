
## Main Ideas

Parallel execution for IO (asyncio) or CPU bound (multiprocessing + cluster computing) to enable all kinds of creative mixing and matching between LLM based agents, 

Data flow through task dependency DAGs, and state machines with each state corresponding to a DAG.

Formalized (schematized) dialogue between agents through (NATS based) message bus.

Simple Dependency Injection to enable flexible agent self improvement by using NATS, Postgres and/or Weaviate vector database as memory stores.



## Motivation


Inspired by a short talk by Andrew Ng on the potential of multi-agent systems, and reading up on Langchain's LCEL, Langgraph, Autogen, GPTSwarm, MetaGPT, LLM based genetic programming etc, I wanted to try to build something that combined

- distributed computing to allow easy parallelization of LLM based (calling remote LLMs or running your own open source ones locally) and non-LLM based (e.g. ML, classical AI algorithms) workflows
- iterative workflows using HSMs e.g. the write code - run it - re-write it based on error messages etc, which can eventually be extended to implement genetic programming loops (initialization, evaluation, LMX based mutation, and so on...)
- schematized dialogue -- i.e. the standard operating procedure SOP based approach used by MetaGPT combined with inter-agent  (or inter-task where each task contains langchain/langgraph agents/agent teams) communication NATS as a messaging bus
- defining steps in multi-agent workflows using dependency injection and state-less execution similar to web frameworks like FastAPI
- intuitive internal DSLs for defining workflows used by Apache Airflow


There's still a long way to go to get to all this :)

## Features

### Current
- Specify your multi-agent workflows using intuitive internal DSL to define Data Flow DAGs and State Machines (WIP).
- Specify your workflows as parallelized tasks with A. schematized inputs/outputs (a la MetaGPT) and B. FastAPI style dependency injection so you can use mix and match how you use message bus channels, Weaviate collections, distributed KV stores in your agent or multi-agent based task.
- Parallelize workflows with multiple processes single machine, or scale on a cluster.
- In addition to schematized dataflow between state machine states and task DAGS, also support ad hoc communications between agents using a NATS based messaging bus.
- Combine large proprietary LLMs with small open source LLMs (Large LLMs are tool-makers/library writes, small LLMs as tool runners). (Partial)
- Combine IO bound, CPU bound, and GPU bound tasks into your multi-agent workflows. (1. ML + classical AI + LLM-MAS + Anything (E.g. multimedia processing) 2. ... 3. Profit?)

### Planned
- Easy to implement agent self-improvement, persistence and memory with NATS Key Value store, Postgres and Weaviate (Vector) Databases.
- Formalized (schematized) dialog (a la MetaGPT), or natural language (a la Autogen) between agents using ad hoc messaging channels. (Partial)
- Let your LLM based multi-agent workflows create and/or modify your LLM based multi-agent workflows...
