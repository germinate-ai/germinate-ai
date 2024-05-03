import typing as typ

import networkx as nx

from .definition import TaskDefinition



def build_tasks_dag(tasks: typ.Sequence[TaskDefinition]) -> nx.DiGraph:
    """Build NetworkX Directed Graph from a list of tasks."""
    g = nx.DiGraph()
    for task in tasks:
        g.add_node(task.name, task=task)
        for dep in task.parents:
            g.add_edge(dep.name, task.name)
    return g


def is_dag(g: nx.DiGraph) -> bool:
    """Check that the graph is a DAG."""
    return nx.is_directed_acyclic_graph(g)

def topological_generations(g: nx.DiGraph) -> typ.Generator[list[str], None, None]:
    """Get topologically sorted generations from a DAG."""
    if not nx.is_directed_acyclic_graph(g):
        raise TypeError("Invalid tasks specification: not a DAG")

    return nx.topological_generations(g)


def toposort_tasks_phases(tasks: typ.Sequence[TaskDefinition]) -> typ.Generator[list[str], None, None]:
    """Get "phases" of tasks from a list of tasks, so that all the tasks in a single phase can be run in parallel."""
    g = build_tasks_dag(tasks)
    phases = topological_generations(g)
    return phases
