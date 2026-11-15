
from langgraph.graph import StateGraph, START, END

from orchestration.inbox_triage_state import InboxTriageState

from orchestration.inbox_triage_nodes import (
    inbox_triage_node
)


def build_inbox_triage_graph():

    graph = StateGraph(InboxTriageState)

    graph.add_node(
        "inbox_triage",
        inbox_triage_node
    )

    graph.add_edge(
        START,
        "inbox_triage"
    )

    graph.add_edge(
        "inbox_triage",
        END
    )

    return graph.compile()


inbox_triage_graph = build_inbox_triage_graph()
