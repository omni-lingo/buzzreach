"""Cross-module contract for User data.

This DTO is the boundary contract between the auth module and all consumers
(AUTH-002, API-001). It intentionally excludes sensitive fields
(password_hash, api_key) to prevent accidental leakage.
"""

from uuid import UUID

from pydantic import BaseModel


class UserData(BaseModel):
    """Public-safe user representation for cross-module use.

    Imported by AUTH-002 (JWT service) and API-001 (opportunities API).
    Never includes password_hash or api_key.
    """

    id: UUID
    username: str
    email: str
    is_active: bool
