import pytest

from germinate_ai.workflows.metagpt import workflow

def test_workflow_def():
    assert workflow.name == "simple_metagpt"


def test_state_def():
    design = workflow.states[0]
    assert design.name == "design"

    assert len(design.tasks) == 2


def test_state_tasks_dag():
    design = workflow.states[0]
    
    pm, sa = design.tasks

    assert len(pm.parents) == 0
    assert len(sa.parents) == 1

    assert len(pm.children) == 1
    assert len(sa.children) == 0

    assert pm in sa.parents
    assert sa in pm.children


def test_state_condition_def():
    design = workflow.states[0]

    assert len(design._conditions) > 0
    
    cond = design._conditions[0]
    assert cond.name == "design_is_satisfactory"