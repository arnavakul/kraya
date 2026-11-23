
import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.abspath(os.path.join(_current_dir, ".."))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

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


if __name__ == "__main__":
    import os
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "documents"))
    os.makedirs(docs_dir, exist_ok=True)
    out_path = os.path.join(docs_dir, "langgraph_procurement_graph.png")
    try:
        img_bytes = procurement_graph.get_graph().draw_mermaid_png()
        with open(out_path, "wb") as f:
            f.write(img_bytes)
        print(f"Graph image generated successfully at: {out_path}")
    except Exception as e:
        print(f"Error generating graph image: {e}")
