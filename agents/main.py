
from agents.intake.agent import run_intake_agent


def main():

    print("\n========== KRAYA INTAKE AGENT ==========\n")

    user_input = input(
        "Enter your procurement requirement:\n> "
    )

    existing_requirement = None

    while True:

        result = run_intake_agent(
            user_input=user_input,
            existing_requirement=existing_requirement
        )

        print("\n========== INTAKE RESULT ==========\n")

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
