class AmbigousQueryError(RuntimeError):
    """
    Raised when a query should return a single value but
    multiple possible responses were found.
    """


class EmptyQueryError(RuntimeError):
    """
    Raised when a query should return a single value but
    no possible responses were found.
    """