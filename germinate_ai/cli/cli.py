import sys
from typing import Annotated, Optional

from loguru import logger
import typer

from germinate_ai.worker.main import start_worker_node
from germinate_ai.coordinator.main import start_coordinator
from germinate_ai.data.database import create_tables

from germinate_ai.cli.run_workflow import import_and_run_workflow


cli = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)


@cli.command()
def api():
    """Start the germinate-ai REST API server."""
    logger.debug("api stub")


@cli.command()
def coordinator():
    """Start the germinate-ai Coordinator."""
    start_coordinator()


@cli.command()
def worker(
    n_procs: Annotated[
        int, typer.Option("--num-procs", "-n", help="Number of worker processes")
    ] = None,
):
    """Start a germinate-ai Worker."""

    # TODO importing manually so tasks get registered
    # TODO IMPORTANT
    from ..workflows.metagpt.main import workflow

    logger.info(f"TEMP DEV - Manually imported workflow preset: {workflow.name}")

    start_worker_node(n_procs=n_procs)


@cli.command()
def workflow(
    import_path: Annotated[
        str,
        typer.Argument(
            help='Path to module containing workflow e.g. "workflows.metagpt.main:workflow"'
        ),
    ],
    input_data_json: Annotated[
        Optional[str],
        typer.Argument(help="Input data for first task(s) as JSON string."),
    ] = None,
):
    """Run workflow from a module.

    Example usage:
        germinate workflow simple_metagpt:workflow
    """
    import_and_run_workflow(import_path, input_data_json=input_data_json)


@cli.command()
def db():
    """Dev: Create DB tables."""
    create_tables()


@cli.callback()
def main(verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False):
    log_level = "INFO"
    log_format = (
        "<level>{level: <8}</level> | "
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{message}</level> | "
        "<light-blue>{process.name}::{thread.name}</light-blue>"
        # "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>"
    )
    if verbose:
        # Set logging level to debug
        log_level = "DEBUG"
    logger.remove(0)
    # , format=log_format
    logger.add(sys.stderr, level=log_level, format=log_format)
