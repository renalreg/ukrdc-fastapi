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


class MirthChannelError(RuntimeError):
    """Error getting Mirth channel info"""


class NoActiveMembershipError(RuntimeError):
    """No active membership of the required type was found on this record"""


class MissingFacilityError(RuntimeError):
    """No facility configuration found for this facility code"""


class PKBOutboundDisabledError(RuntimeError):
    """PKB outbound sending disabled for this facility"""
