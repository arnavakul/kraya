
from langchain_core.prompts import ChatPromptTemplate

from tools.shared.llm import get_llm

from pydantic_models.requirement_draft import (
    RequirementDraft
)

from agents.intake.prompts import (
    INTAKE_SYSTEM_PROMPT
)


prompt = ChatPromptTemplate.from_messages([

    ("system", INTAKE_SYSTEM_PROMPT),

    (
        "human",
        """
        Previously extracted requirement:

        {existing_requirement}

        Latest user message:

        {user_input}

        Extract the updated requirement.
        Preserve previous information unless the
        user explicitly changes or corrects it.
        """
    )
])


def parse_requirement(
    user_input: str,
    existing_requirement: dict | None = None
) -> RequirementDraft:

    if not user_input.strip():
        raise ValueError("User input cannot be empty")

    llm = get_llm(temperature=0)

    structured_llm = llm.with_structured_output(
        RequirementDraft,
        method="json_schema"
    )

    chain = prompt | structured_llm

    result = chain.invoke({

        "existing_requirement": (
            existing_requirement or {}
        ),

        "user_input": user_input
    })

    return result
