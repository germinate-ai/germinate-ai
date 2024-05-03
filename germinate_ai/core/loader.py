import importlib
import os
import sys
import typing as typ
from types import ModuleType
from pathlib import Path

from loguru import logger

from germinate_ai.core.exceptions import WorkflowImportException
from germinate_ai.core.workflows import Workflow


def import_workflow(
    workflow_import_path: str,
    *,
    working_dir: typ.Optional[str] = None,
):
    """
    Import a workflow instance from the given module.

    Example usage:
        # ./simple_metagpt.py
        import_workflow("simple_metagpt:workflow")
        import_workflow("simple_metagpt:workflow_v2")

        # ./my_project/workflows/simple_metagpt.py
        import_workflow("workflows.simple_metagpt:workflow", working_dir="./my_project")
    """

    module_name, var_name = parse_import_path(workflow_import_path)
    module = import_module(module_name, working_dir=working_dir)

    return get_workflow_from_module(module, var_name=var_name)


def get_workflow_from_module(module: ModuleType, var_name: str = None) -> Workflow:
    """Get workflow from the module.

    Get the workflow stored in `var_name`, or the first workflow defined from the module.
    """
    workflow = None
    if var_name:
        # get workflow with matching variable name
        workflow = _get_workflow_with_name(module.__dict__, var_name)
    else:
        # first Workflow instance found
        workflow = _get_first_workflow(module.__dict__)

    if workflow is not None:
        return workflow

    raise WorkflowImportException("Could not find any workflows")


def parse_import_path(workflow_import_path: str) -> typ.Tuple[str, str]:
    module_name, _, var_name = workflow_import_path.partition(":")
    if not module_name:
        raise WorkflowImportException("Invalid workflow import path")
    return module_name, var_name


def import_module(module_name: str, *, working_dir: typ.Optional[str] = None):
    logger.debug(f"importing module {module_name}")

    orig_wd = Path.cwd()
    changed_dir = False
    added_to_sys_path = False

    try:
        if working_dir is not None:
            # change to working dir if provided
            working_dir = Path(working_dir).expanduser().resolve()
            os.chdir(working_dir)
            changed_dir = True
        else:
            working_dir = orig_wd

        if working_dir not in sys.path:
            # add working dir to sys path
            sys.path.insert(0, working_dir)
            added_to_sys_path = True

        # import
        try:
            module = importlib.import_module(module_name, package=working_dir)
        except ImportError as e:
            raise ImportError(f"Could not import `{module_name}`: {e}")

        return module

    except ImportError:
        raise
    finally:
        if changed_dir:
            os.chdir(orig_wd)
        if added_to_sys_path:
            sys.path.remove(working_dir)


def _get_workflow_with_name(module_dict: dict, name: str) -> typ.Union[Workflow, None]:
    """Get varname from module dict."""
    for var_name, obj in module_dict.items():
        if var_name == name and isinstance(obj, Workflow):
            return obj

    return None


def _get_first_workflow(module_dict: dict) -> typ.Union[Workflow, None]:
    """Get first workflow from module dict."""
    for obj in module_dict.values():
        if isinstance(obj, Workflow):
            return obj

    return None
