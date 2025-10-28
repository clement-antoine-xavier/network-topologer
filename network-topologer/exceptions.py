"""Custom exceptions for network-topologer traceroute logic."""


class TracerouteError(Exception):
    """Base class for traceroute related errors."""

    pass


class DNSResolveError(TracerouteError):
    """Raised when DNS resolution of the destination fails."""

    pass


class TraceroutePermissionError(TracerouteError):
    """Raised when sending packets is denied due to permissions (need root)."""

    pass
