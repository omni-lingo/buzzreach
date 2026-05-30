"""Cross-module contract for JWT token payload (AUTH-002).

This DTO represents the decoded JWT claims. It is used by the JWT service
for encoding/decoding and by consumers (API-001) for inspecting token
contents in tests and middleware.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class JwtPayload(BaseModel):
    """Decoded JWT token claims.

    Imported by AUTH-002 (JWT service) and API-001 (route auth dependency).
    """

    sub: UUID
    iat: datetime
    exp: datetime
