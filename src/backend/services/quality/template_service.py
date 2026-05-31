"""Template service for CRUD and interpolation (QUALITY-003).

Pure business logic with no HTTP dependencies. Database access via
injected Session. Raises AppError for recoverable failures.

Cross-module contracts:
- Used by draft editor (FEAT-001)
- Stored per user (AUTH-001)
"""

import logging
import re
import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from contracts.quality.draft_template import (
    TemplateCreateRequest,
    TemplateUpdateRequest,
)
from src.backend.errors import AppError
from src.backend.models.draft_template import DraftTemplate
from src.backend.services.quality.seed_templates import GLOBAL_TEMPLATES

log = logging.getLogger("buzzreach.quality.templates")

_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


class TemplateService:
    """Manages draft template CRUD, seeding, and interpolation."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_template(
        self,
        req: TemplateCreateRequest,
        user_id: _uuid.UUID,
    ) -> DraftTemplate:
        """Create a custom template owned by the given user."""
        tpl = DraftTemplate(
            name=req.name,
            category=req.category.value,
            description=req.description,
            text=req.text,
            user_id=user_id,
        )
        self._session.add(tpl)
        self._session.commit()
        log.info(
            "Template created",
            extra={"template_id": str(tpl.id), "user_id": str(user_id)},
        )
        return tpl

    def list_templates(
        self,
        user_id: _uuid.UUID | None = None,
        category: str | None = None,
        search: str | None = None,
    ) -> list[DraftTemplate]:
        """List templates: global + user-owned, with optional filters."""
        query = self._session.query(DraftTemplate)
        if user_id is not None:
            query = query.filter(
                or_(
                    DraftTemplate.user_id.is_(None),
                    DraftTemplate.user_id == user_id,
                )
            )
        else:
            query = query.filter(DraftTemplate.user_id.is_(None))

        if category is not None:
            query = query.filter(DraftTemplate.category == category)

        if search is not None:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    DraftTemplate.name.ilike(pattern),
                    DraftTemplate.description.ilike(pattern),
                )
            )

        return list(query.order_by(DraftTemplate.name).all())

    def get_template(self, template_id: _uuid.UUID) -> DraftTemplate:
        """Fetch a single template by ID or raise TEMPLATE_NOT_FOUND."""
        tpl = self._session.get(DraftTemplate, template_id)
        if tpl is None:
            raise AppError(
                code="TEMPLATE_NOT_FOUND",
                message="Template not found",
            )
        return tpl

    def update_template(
        self,
        template_id: _uuid.UUID,
        req: TemplateUpdateRequest,
        user_id: _uuid.UUID,
    ) -> DraftTemplate:
        """Update a user-owned template. Global templates cannot be edited."""
        tpl = self.get_template(template_id)
        self._assert_owned(tpl, user_id)

        if req.name is not None:
            tpl.name = req.name
        if req.category is not None:
            tpl.category = req.category.value
        if req.description is not None:
            tpl.description = req.description
        if req.text is not None:
            tpl.text = req.text
        tpl.updated_at = datetime.now(UTC)

        self._session.commit()
        log.info(
            "Template updated",
            extra={
                "template_id": str(template_id),
                "user_id": str(user_id),
            },
        )
        return tpl

    def delete_template(
        self,
        template_id: _uuid.UUID,
        user_id: _uuid.UUID,
    ) -> None:
        """Delete a user-owned template. Global templates cannot be deleted."""
        tpl = self.get_template(template_id)
        self._assert_owned(tpl, user_id)

        self._session.delete(tpl)
        self._session.commit()
        log.info(
            "Template deleted",
            extra={
                "template_id": str(template_id),
                "user_id": str(user_id),
            },
        )

    def seed_global_templates(self) -> None:
        """Insert global templates if they don't already exist.

        Idempotent: skips templates whose name already exists as global.
        """
        existing = {
            t.name
            for t in self._session.query(DraftTemplate)
            .filter(DraftTemplate.user_id.is_(None))
            .all()
        }

        for seed in GLOBAL_TEMPLATES:
            if seed.name in existing:
                continue
            tpl = DraftTemplate(
                name=seed.name,
                category=seed.category,
                description=seed.description,
                text=seed.text,
                user_id=None,
            )
            self._session.add(tpl)

        self._session.commit()
        log.info("Global templates seeded")

    @staticmethod
    def interpolate(text: str, variables: dict[str, str]) -> str:
        """Replace {placeholder} tokens with values from variables.

        Unknown placeholders are left as-is so the user can fill them.
        """
        def _replace(match: re.Match[str]) -> str:
            key = match.group(1)
            return variables.get(key, match.group(0))

        return _PLACEHOLDER_RE.sub(_replace, text)

    @staticmethod
    def _assert_owned(tpl: DraftTemplate, user_id: _uuid.UUID) -> None:
        """Raise if the template is global or owned by another user."""
        if tpl.user_id is None or tpl.user_id != user_id:
            raise AppError(
                code="TEMPLATE_NOT_OWNED",
                message="Cannot modify a template you don't own",
            )
