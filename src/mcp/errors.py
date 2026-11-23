class PublishStoppedArchived(Exception):
    pass


class MCPError(Exception):
    pass


class MCPConnectionError(MCPError):
    pass


class MCPRateLimitError(MCPConnectionError):
    pass


class MCPAuthError(MCPError):
    pass


class MCPConnectionExpired(MCPError):
    pass


class MCPNotFoundError(MCPError):
    pass


class MCPToolNotFoundError(MCPError):
    pass


class MCPToolRefused(MCPError):
    pass


class MCPAccountNotPinned(MCPError):
    pass


class MCPMissingSetting(MCPError):
    pass


class MCPMalformedResponse(MCPError):
    pass
