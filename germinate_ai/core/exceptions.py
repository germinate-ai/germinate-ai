class GerminateAIException(Exception):
    """Base class for Germinate AI exceptions."""

    pass


class InvalidWorkflowException(GerminateAIException):
    """Workflow is invalid."""

    pass


class InvalidTasksDagException(GerminateAIException):
    """Tasks DAG is invalid."""

    pass

class WorkflowFileNotFoundException(GerminateAIException):
    """Could not find the specified workflow definition module file."""

    pass


class MessageBusUnavailableException(GerminateAIException):
    """Messaging bus backend in not reachable."""

    pass


class DatabaseUnavailableException(GerminateAIException):
    """Database backend in not reachable."""

    pass


class InvalidConfigurationException(GerminateAIException):
    """The configuration is invalid."""

    pass


class WorkflowImportException(GerminateAIException):
    """Failed to import the specified workflow definition."""

    pass


class InvalidArgumentsException(GerminateAIException):
    """Invalid arguments."""

    pass
