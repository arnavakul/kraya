
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from orchestration.state import ProcurementState

from orchestration.nodes import (
    intake_node,
    supplier_discovery_node,
    rfq_drafting_node
)

from orchestration.approval import rfq_approval_node

from orchestration.routing import (
    route_after_intake,
    route_after_supplier_discovery,
    route_after_rfq_drafting
)


def build_procurement_graph():

    graph = StateGraph(ProcurementState)

    graph.add_node("intake", intake_node)
    graph.add_node("supplier_discovery", supplier_discovery_node)
    graph.add_node("rfq_drafting", rfq_drafting_node)
    graph.add_node("approval", rfq_approval_node)

    graph.add_edge(START, "intake")

    graph.add_conditional_edges(
        "intake",
        route_after_intake,
        {
            "supplier_discovery": "supplier_discovery",
            "end": END
        }
    )

    graph.add_conditional_edges(
        "supplier_discovery",
        route_after_supplier_discovery,
        {
            "rfq_drafting": "rfq_drafting",
            "end": END
        }
    )

    graph.add_conditional_edges(
        "rfq_drafting",
        route_after_rfq_drafting,
        {
            "approval": "approval",
            "end": END
        }
    )

    graph.add_edge("approval", END)

    checkpointer = InMemorySaver()

    return graph.compile(checkpointer=checkpointer)


procurement_graph = build_procurement_graph()
