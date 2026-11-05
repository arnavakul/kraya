from fastapi import FastAPI
from evaluation.router import router as evaluation_router
from agents.intake.agent import run_intake_agent

app = FastAPI(
    title="Kraya — AI Agent Microservice",
    description="Python AI/ML service for quote parsing, XGBoost risk evaluation, and SHAP feature attributions.",
    version="1.0.0"
)

# Register the Evaluation Agent router
app.include_router(evaluation_router)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "UP", "service": "kraya-agents"}


def main():

    print("\n========== KRAYA INTAKE AGENT ==========")

    user_input = input(
        "Enter your procurement requirement:\n> "
    )

    existing_requirement = None

    while True:

        result = run_intake_agent(
            user_input=user_input,
            existing_requirement=existing_requirement
        )

        print("\n========== INTAKE RESULT ==========")

        if result["status"] == "validated":

            print("Requirement successfully validated.")

            print("\nFinal Requirement:\n")

            print(result["requirement"])

            break

        elif result["status"] == "needs_clarification":

            print("Additional information required.\n")

            existing_requirement = result[
                "requirement_draft"
            ]

            for question in result["clarification_questions"]:
                print("-", question)

            user_input = input(
                "\nYour response:\n> "
            )

        else:

            print("Intake failed:", result["errors"])
            break


if __name__ == "__main__":
    main()
