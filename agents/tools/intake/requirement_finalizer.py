
from pydantic_models.requirement import Requirement
from pydantic_models.requirement_draft import RequirementDraft


def finalize_requirement(
    draft: RequirementDraft
) -> Requirement:

    data = draft.model_dump(
        exclude_none=True
    )

    # INR as the default only when no other
    # currency was specified and policy allows it.
    data.setdefault("currency", "INR")

    return Requirement(**data)
