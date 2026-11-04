
from agents.intake.prompts import INTAKE_SYSTEM_PROMPT

from tools.intake.requirement_parser import (
    parse_requirement
)

from tools.intake.requirement_validator import (
    validate_requirement
)

from tools.intake.clarification_manager import (
    generate_clarification_questions
)

from tools.intake.requirement_finalizer import (
    finalize_requirement
)


def merge_requirement_drafts(
    previous: dict | None,
    new_draft
) -> dict:

    """
    Preserve previously collected information
    when the user answers clarification questions.
    """

    merged = dict(previous or {})

    new_data = new_draft.model_dump(
        mode="json",
        exclude_none=True
    )

    for key, value in new_data.items():

        if value is None:
            continue

        if key in ["mandatory_constraints", "preferences"]:

            merged[key] = list(dict.fromkeys(
                merged.get(key, []) + value
            ))

        else:

            merged[key] = value

    return merged


def run_intake_agent(
    user_input: str,
    existing_requirement: dict | None = None
):

    # Parse the request using Gemini
    draft = parse_requirement(
        user_input=user_input,
        existing_requirement=existing_requirement
    )

    # Merge newly extracted information
    merged_data = merge_requirement_drafts(
        existing_requirement,
        draft
    )

    # Create an updated draft
    from pydantic_models.requirement_draft import (
        RequirementDraft
    )

    updated_draft = RequirementDraft(
        **merged_data
    )

    # Validate
    validation = validate_requirement(
        updated_draft
    )

    # Handle missing or invalid information
    if not validation["valid"]:

        questions = generate_clarification_questions(
            validation["missing_fields"],
            validation["errors"]
        )

        return {

            "status": "needs_clarification",

            "requirement_draft": updated_draft.model_dump(
                mode="json"
            ),

            "missing_fields": validation["missing_fields"],

            "clarification_questions": questions,

            "errors": validation["errors"],

            "requirement": None
        }

    # Finalize requirement
    requirement = finalize_requirement(
        updated_draft
    )

    return {

        "status": "validated",

        "requirement_draft": updated_draft.model_dump(
            mode="json"
        ),

        "missing_fields": [],

        "clarification_questions": [],

        "errors": [],

        "requirement": requirement.model_dump(
            mode="json"
        )
    }
