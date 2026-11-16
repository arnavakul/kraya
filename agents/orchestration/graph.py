
from langgraph.graph import StateGraph, START, END

from orchestration.state import ProcurementState

from orchestration.nodes import (
    intake_node,
    supplier_discovery_node,
    rfq_drafting_node,
    policy_guardrails_node,
)
from orchestration.approval import (
    create_rfq_approval_requests_node,
    rfq_approval_node,
)

from orchestration.routing import (
    route_after_intake,
    route_after_supplier_discovery,
    route_after_rfq_drafting,
    route_after_policy_guardrails,
    route_after_approval_requests,
)


def build_procurement_graph(checkpointer=None):

    graph = StateGraph(ProcurementState)

    # Register nodes
    graph.add_node("intake", intake_node)
    graph.add_node("supplier_discovery", supplier_discovery_node)
    graph.add_node("rfq_drafting", rfq_drafting_node)
    graph.add_node("policy_guardrails", policy_guardrails_node)
    graph.add_node("approval_requests", create_rfq_approval_requests_node)
    graph.add_node("approval", rfq_approval_node)

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

    graph.add_conditional_edges(
        "rfq_drafting",
        route_after_rfq_drafting,
        {
            "approval": "policy_guardrails",
            "end": END,
        },
    )

    graph.add_conditional_edges(
        "policy_guardrails",
        route_after_policy_guardrails,
        {
            "approval_requests": "approval_requests",
            "end": END,
        },
    )

    graph.add_conditional_edges(
        "approval_requests",
        route_after_approval_requests,
        {
            "approval": "approval",
            "end": END,
        },
    )

    graph.add_edge("approval", END)

    return graph.compile(checkpointer=checkpointer)


procurement_graph = build_procurement_graph()
