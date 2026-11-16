
from langgraph.graph import StateGraph, START, END

from orchestration.inbox_triage_state import InboxTriageState

from orchestration.inbox_triage_nodes import (
    inbox_triage_node,
    evaluation_node,
)
from orchestration.negotiation import negotiation_node


def build_inbox_triage_graph():

    graph = StateGraph(InboxTriageState)

    graph.add_node(
        "inbox_triage",
        inbox_triage_node
    )

    graph.add_node("evaluation", evaluation_node)
    graph.add_node("negotiation", negotiation_node)

    graph.add_edge(
        START,
        "inbox_triage"
    )

    graph.add_edge(
        "inbox_triage",
        "evaluation"
    )

    graph.add_edge("evaluation", "negotiation")
    graph.add_edge("negotiation", END)

    return graph.compile()


inbox_triage_graph = build_inbox_triage_graph()
