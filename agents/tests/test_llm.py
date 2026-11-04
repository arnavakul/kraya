
from tools.shared.llm import get_llm


def test_gemini_connection():

    llm = get_llm()

    response = llm.invoke(
        "Reply with exactly: Kraya Gemini connection successful"
    )

    print(response.content)
    assert response.content