
from langgraph.graph import StateGraph, START, END

from orchestration.state import ProcurementState

from orchestration.nodes import (
    intake_node,
    supplier_discovery_node,
    rfq_drafting_node
)

from orchestration.routing import (
    route_after_intake,
    route_after_supplier_discovery
)


def build_procurement_graph():

    graph = StateGraph(ProcurementState)

    # Register nodes
    graph.add_node("intake", intake_node)
    graph.add_node("supplier_discovery", supplier_discovery_node)
    graph.add_node("rfq_drafting", rfq_drafting_node)

    # Starting point
    graph.add_edge(START, "intake")

    # Intake routing
    graph.add_conditional_edges(
        "intake",
        route_after_intake,
        {
            "supplier_discovery": "supplier_discovery",
            "end": END
        }
    )

    # Supplier discovery routing
    graph.add_conditional_edges(
        "supplier_discovery",
        route_after_supplier_discovery,
        {
            "rfq_drafting": "rfq_drafting",
            "end": END
        }
    )

    # Final node
    graph.add_edge("rfq_drafting", END)

    return graph.compile()


procurement_graph = build_procurement_graph()
