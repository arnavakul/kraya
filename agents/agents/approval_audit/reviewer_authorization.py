
from repositories.user_repository import UserRepository


class ReviewerAuthorizationChecker:
    """Verifies whether a user can review an approval request."""

    ALLOWED_REVIEWER_ROLES = {"ORG_ADMIN"}

    def __init__(self, user_repository=None):
        self.user_repository = user_repository or UserRepository()

    def validate_reviewer(
        self,
        reviewer_user_id: str,
        organization_id: str,
        requester_user_id: str,
    ) -> None:

        if not reviewer_user_id or not reviewer_user_id.strip():
            raise ValueError("Reviewer user ID is required.")

        if reviewer_user_id == requester_user_id:
            raise ValueError("Requester cannot approve their own request.")

        user = self.user_repository.get_user_by_id(reviewer_user_id)

        if user is None:
            raise ValueError("Reviewer does not exist.")

        if user["organization_id"] != organization_id:
            raise ValueError("Reviewer belongs to another organization.")

        if user["status"].upper() != "ACTIVE":
            raise ValueError("Reviewer account is not active.")

        if user["role"].upper() not in self.ALLOWED_REVIEWER_ROLES:
            raise ValueError("Reviewer does not have approval permission.")
