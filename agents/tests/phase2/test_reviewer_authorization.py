
from unittest.mock import Mock

import pytest

from agents.approval_audit.reviewer_authorization import (
    ReviewerAuthorizationChecker,
)


def create_user(**overrides):
    user = {
        "id": "user-2",
        "organization_id": "org-1",
        "role": "ORG_ADMIN",
        "status": "ACTIVE",
    }
    user.update(overrides)
    return user


def create_checker(user):
    repository = Mock()
    repository.get_user_by_id.return_value = user

    checker = ReviewerAuthorizationChecker(
        user_repository=repository
    )
    return checker, repository


def test_active_org_admin_is_authorized():
    checker, _ = create_checker(create_user())

    checker.validate_reviewer("user-2", "org-1", "user-1")


def test_reviewer_from_another_organization_is_rejected():
    checker, _ = create_checker(
        create_user(organization_id="org-2")
    )

    with pytest.raises(ValueError, match="another organization"):
        checker.validate_reviewer("user-2", "org-1", "user-1")


def test_inactive_reviewer_is_rejected():
    checker, _ = create_checker(
        create_user(status="INACTIVE")
    )

    with pytest.raises(ValueError, match="not active"):
        checker.validate_reviewer("user-2", "org-1", "user-1")


def test_unauthorized_role_is_rejected():
    checker, _ = create_checker(
        create_user(role="BUYER")
    )

    with pytest.raises(ValueError, match="approval permission"):
        checker.validate_reviewer("user-2", "org-1", "user-1")


def test_requester_cannot_review_own_request():
    checker, _ = create_checker(create_user())

    with pytest.raises(ValueError, match="own request"):
        checker.validate_reviewer("user-1", "org-1", "user-1")


def test_nonexistent_reviewer_is_rejected():
    checker, _ = create_checker(None)

    with pytest.raises(ValueError, match="does not exist"):
        checker.validate_reviewer("user-2", "org-1", "user-1")
