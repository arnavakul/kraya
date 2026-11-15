
from langgraph.graph import StateGraph, START, END

from orchestration.state import ProcurementState

from orchestration.nodes import (
    intake_node,
    supplier_discovery_node
)

from orchestration.routing import route_after_intake


def build_procurement_graph():

    graph = StateGraph(ProcurementState)

    # Register nodes
    graph.add_node("intake", intake_node)
    graph.add_node(
        "supplier_discovery",
        supplier_discovery_node
    )

    # Starting point
    graph.add_edge(START, "intake")

    # Conditional routing
    graph.add_conditional_edges(
        "intake",
        route_after_intake,
        {
            "supplier_discovery": "supplier_discovery",
            "end": END
        }
    )

    # Final node
    graph.add_edge("supplier_discovery", END)

    return graph.compile()


procurement_graph = build_procurement_graph()
