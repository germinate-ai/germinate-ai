from germinate_ai import GerminateEngine, TaskExecutor, Workflow, Channel

# Agent memory
# Input structure
# Natlang vs structured channels

# Agent = model + prompt + tools + memory
# Agent team = [agent, ...] + channel ???
# blackboard channel - blackboard architecture


# combine the iterative capability of HSMs with the easy toposort + scheduling pipelining
# you can do with DAGs
# Workflow -> stages (HSM) -> steps (DAG)
# Workflow started -> ??
# Stage queued -> job
# each queued step -> task

# nice to have
# - DSP
#       - ??
# - evolution
#       - population from workflow
#               - variation of tree?
#               - workflow genes (e.g. DSL repr) -> LLM generates variations
#               - same workflow but different prompts, agent architectures, memory subsets etc
#               - all of the above
#       - run all
#       - fitness function
#       - mutate somehow
#       - repeat n times
#       - API?
#       - germinate.evolve()
# - competition and debate instead of just cooperation bet/n agents
# - behavior trees

# channels - HOW
# 1. Each channel subscribed to
#       - Put in prompt under a section e.g.
#         """
#           You are...
#           ...
#           # Original instructions, etc.
#           # Subscribed channels
#           ## Channel1
#           Agent1: Lets do X
#           Agent2: Lets do Y
#           ...
#         """
# 2. Blackboard channel
#       Agent 1: Proposal A
#       Agent 2: Proposal B
#       Agent 3: Proposal A but with X
#       Architect: I decide proposal B with X
#       Or: voted on proposal: Proposal A wins
# etc
#  3. Planning channel
#       Agent team: Coder, ARchitect, Project manager
#       Coder: Here's my plan
#       Architect: My review is:
#       Project manager: My comments are
#       Coder: Here's my updated plan
#       .......
#
#        That is:
#           State machine inside the step
#           Max N iterations



# Schema
# API
# UI

# 1 day
#  Start iteratively

# 1. prompt -> pm task runs -> prd
# 2. prd -> architect task runs in next stage

# e.g. 1. prompt -> pm
# planning chat - RFCs
# everyone keeps two sets of notes - notes for self for later, RFC to make proposals
# PM + architect combine, decides between proposals, summarize
# PM -> makes a PRD

# 2. prd -> system design
# ^^ similar

# 3. coding
# executable + feedback
# if N failures
# RFC again


# 2 hours
# A need an API
# Look at API project
# CRUD
# Create schemas -- no API updates - updates <- workers
# need 

# B dist jobs queue - task runner system
# 1. user defines a custom task executor
# 2. user schedules a dag
#        -< directly to nats
#        design 1 -agent -> custom task -> design 2-agent > out
# 3. one node -> must use custom task exec
#       others - existing task exec
# 4. must run appropriately ^^


# schema
# workflow -> workflow run
# stage -> job
# step -> task
# team -> swarm

# run in notebooks!!
# embed langchain agents graphs -> tasks

# cockroachdb docker compose

# =======================================================================

# Self improvement
# ---------------
# Each agent learns from their past work
# Include relevant text from common channels
# Docs
# summarize and store in a different collection - similar to human memory
#   create new collection -> summarize and move
#   -- aka dreaming/ long term memory formations
#   -- short term is detailed and long -- long term is short and summarized
#   -- include 2nd brain -- use long term to re-refer to short term history
#   -- allow LLM to write permanent memory notes 
# include some of it in subsequent tasks - RAG
