"""Error types for team management (ADMIN-001)."""


class TeamError(Exception):
    """Base error for team operations."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class TeamNotFoundError(TeamError):
    """Raised when a team does not exist."""

    def __init__(self, team_id: str = "") -> None:
        super().__init__(
            code="TEAM_NOT_FOUND",
            message=f"Team not found: {team_id}",
        )


class MemberNotFoundError(TeamError):
    """Raised when a team member does not exist."""

    def __init__(self) -> None:
        super().__init__(
            code="MEMBER_NOT_FOUND",
            message="Team member not found",
        )


class InvitationNotFoundError(TeamError):
    """Raised when an invitation token is invalid."""

    def __init__(self) -> None:
        super().__init__(
            code="INVITATION_NOT_FOUND",
            message="Invitation not found or invalid token",
        )


class InvitationExpiredError(TeamError):
    """Raised when an invitation has expired."""

    def __init__(self) -> None:
        super().__init__(
            code="INVITATION_EXPIRED",
            message="Invitation has expired",
        )


class InvitationUsedError(TeamError):
    """Raised when an invitation has already been used."""

    def __init__(self) -> None:
        super().__init__(
            code="INVITATION_ALREADY_USED",
            message="Invitation has already been used",
        )


class PermissionDeniedError(TeamError):
    """Raised when the user lacks permission for the action."""

    def __init__(self, action: str = "") -> None:
        super().__init__(
            code="PERMISSION_DENIED",
            message=f"Permission denied: {action}",
        )


class PlanLimitError(TeamError):
    """Raised when the team has reached its plan member limit."""

    def __init__(self, limit: int) -> None:
        super().__init__(
            code="PLAN_LIMIT_REACHED",
            message=f"Team member limit reached: {limit}",
        )


class AlreadyMemberError(TeamError):
    """Raised when the user is already a member of the team."""

    def __init__(self) -> None:
        super().__init__(
            code="ALREADY_MEMBER",
            message="User is already a member of this team",
        )


class CannotRemoveOwnerError(TeamError):
    """Raised when trying to remove the team owner."""

    def __init__(self) -> None:
        super().__init__(
            code="CANNOT_REMOVE_OWNER",
            message="Cannot remove the team owner",
        )
