"""Tests for draft template model, service, and API (QUALITY-003).

Covers:
- DraftTemplate model CRUD
- TemplateService business logic (create, list, update, delete, seed)
- Template variable interpolation
- Global vs custom template filtering
- Search/filter by category and name
"""

import uuid

import pytest
from sqlalchemy.orm import Session

from contracts.quality.draft_template import (
    TemplateCategory,
    TemplateCreateRequest,
    TemplateUpdateRequest,
)
from src.backend.errors import AppError
from src.backend.models.draft_template import DraftTemplate
from src.backend.services.quality.template_service import TemplateService
from tests.conftest import make_user


class TestDraftTemplateModel:
    """Unit tests for DraftTemplate ORM model."""

    def test_create_global_template(self, db_session: Session) -> None:
        tpl = DraftTemplate(
            name="Tech Support",
            category="technical",
            description="For programming help threads",
            text="Hi {user_name}, regarding {product_name}...",
            user_id=None,
        )
        db_session.add(tpl)
        db_session.commit()

        row = db_session.get(DraftTemplate, tpl.id)
        assert row is not None
        assert row.name == "Tech Support"
        assert row.user_id is None
        assert row.is_global is True

    def test_create_user_template(self, db_session: Session) -> None:
        user = make_user()
        db_session.add(user)
        db_session.commit()

        tpl = DraftTemplate(
            name="My Template",
            category="casual",
            description="Personal template",
            text="Hey there, check out {product_name}!",
            user_id=user.id,
        )
        db_session.add(tpl)
        db_session.commit()

        row = db_session.get(DraftTemplate, tpl.id)
        assert row is not None
        assert row.user_id == user.id
        assert row.is_global is False

    def test_template_has_timestamps(self, db_session: Session) -> None:
        tpl = DraftTemplate(
            name="Timestamped",
            category="blog",
            description="Test timestamps",
            text="Template {product_name}",
        )
        db_session.add(tpl)
        db_session.commit()

        assert tpl.created_at is not None
        assert tpl.updated_at is not None


class TestTemplateService:
    """Unit tests for TemplateService business logic."""

    def test_create_template(self, db_session: Session) -> None:
        user = make_user()
        db_session.add(user)
        db_session.commit()

        svc = TemplateService(db_session)
        req = TemplateCreateRequest(
            name="Custom Template",
            category=TemplateCategory.REDDIT,
            description="For Reddit threads",
            text="Great question about {product_name}!",
        )
        tpl = svc.create_template(req, user_id=user.id)
        assert tpl.name == "Custom Template"
        assert tpl.user_id == user.id
        assert tpl.category == "reddit"

    def test_list_templates_includes_global(
        self, db_session: Session
    ) -> None:
        user = make_user()
        db_session.add(user)
        db_session.commit()

        svc = TemplateService(db_session)
        svc.seed_global_templates()

        items = svc.list_templates(user_id=user.id)
        global_items = [t for t in items if t.is_global]
        assert len(global_items) >= 5

    def test_list_templates_by_category(
        self, db_session: Session
    ) -> None:
        svc = TemplateService(db_session)
        svc.seed_global_templates()

        items = svc.list_templates(category="technical")
        assert len(items) >= 1
        assert all(t.category == "technical" for t in items)

    def test_list_templates_search(self, db_session: Session) -> None:
        svc = TemplateService(db_session)
        svc.seed_global_templates()

        items = svc.list_templates(search="support")
        assert len(items) >= 1

    def test_update_template(self, db_session: Session) -> None:
        user = make_user()
        db_session.add(user)
        db_session.commit()

        svc = TemplateService(db_session)
        req = TemplateCreateRequest(
            name="Original",
            category=TemplateCategory.CASUAL,
            description="Original desc",
            text="Original text {product_name}",
        )
        tpl = svc.create_template(req, user_id=user.id)

        update = TemplateUpdateRequest(name="Updated Name")
        updated = svc.update_template(tpl.id, update, user_id=user.id)
        assert updated.name == "Updated Name"
        assert updated.description == "Original desc"

    def test_update_global_template_forbidden(
        self, db_session: Session
    ) -> None:
        user = make_user()
        db_session.add(user)
        db_session.commit()

        svc = TemplateService(db_session)
        svc.seed_global_templates()

        items = svc.list_templates()
        global_tpl = next(t for t in items if t.is_global)

        update = TemplateUpdateRequest(name="Hacked")
        with pytest.raises(AppError, match="Cannot modify a template"):
            svc.update_template(
                global_tpl.id, update, user_id=user.id
            )

    def test_delete_template(self, db_session: Session) -> None:
        user = make_user()
        db_session.add(user)
        db_session.commit()

        svc = TemplateService(db_session)
        req = TemplateCreateRequest(
            name="To Delete",
            category=TemplateCategory.BLOG,
            description="Will be deleted",
            text="Delete me {product_name}",
        )
        tpl = svc.create_template(req, user_id=user.id)

        svc.delete_template(tpl.id, user_id=user.id)
        assert db_session.get(DraftTemplate, tpl.id) is None

    def test_delete_global_template_forbidden(
        self, db_session: Session
    ) -> None:
        user = make_user()
        db_session.add(user)
        db_session.commit()

        svc = TemplateService(db_session)
        svc.seed_global_templates()

        items = svc.list_templates()
        global_tpl = next(t for t in items if t.is_global)

        with pytest.raises(AppError, match="Cannot modify a template"):
            svc.delete_template(global_tpl.id, user_id=user.id)

    def test_get_template_by_id(self, db_session: Session) -> None:
        svc = TemplateService(db_session)
        svc.seed_global_templates()

        items = svc.list_templates()
        tpl = svc.get_template(items[0].id)
        assert tpl is not None
        assert tpl.id == items[0].id

    def test_get_template_not_found(self, db_session: Session) -> None:
        svc = TemplateService(db_session)
        with pytest.raises(AppError, match="Template not found"):
            svc.get_template(uuid.uuid4())

    def test_interpolate_variables(self, db_session: Session) -> None:
        svc = TemplateService(db_session)
        text = "Hi {user_name}, check out {product_name} at {product_url}"
        variables = {
            "user_name": "Alice",
            "product_name": "BuzzReach",
            "product_url": "https://buzzreach.app",
        }
        result = svc.interpolate(text, variables)
        assert result == (
            "Hi Alice, check out BuzzReach at https://buzzreach.app"
        )

    def test_interpolate_missing_variable_preserved(
        self, db_session: Session
    ) -> None:
        svc = TemplateService(db_session)
        text = "Hi {user_name}, check {unknown_var}"
        variables = {"user_name": "Alice"}
        result = svc.interpolate(text, variables)
        assert result == "Hi Alice, check {unknown_var}"

    def test_seed_global_templates_idempotent(
        self, db_session: Session
    ) -> None:
        svc = TemplateService(db_session)
        svc.seed_global_templates()
        count_1 = len(svc.list_templates())

        svc.seed_global_templates()
        count_2 = len(svc.list_templates())

        assert count_1 == count_2

    def test_user_templates_isolated(self, db_session: Session) -> None:
        user_a = make_user()
        user_b = make_user()
        db_session.add_all([user_a, user_b])
        db_session.commit()

        svc = TemplateService(db_session)
        svc.create_template(
            TemplateCreateRequest(
                name="A's Template",
                category=TemplateCategory.CASUAL,
                description="User A only",
                text="From A {product_name}",
            ),
            user_id=user_a.id,
        )

        items_b = svc.list_templates(user_id=user_b.id)
        own_items = [t for t in items_b if not t.is_global]
        assert all(t.user_id != user_a.id for t in own_items)
