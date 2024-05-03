import cloudpickle

class ValuePickler(cloudpickle.Pickler):
    """Pickles functions by value so they can be run on workers without the worker initially having a copy of the module."""
    pass