from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Any
import logging
import json
import re

try:
    from evaluation.router import router as evaluation_router
except ModuleNotFoundError as error:
    if error.name != "shap":
        raise
    evaluation_router = None
    logging.getLogger(__name__).warning(
        "Evaluation routes are unavailable because the optional SHAP dependency is missing."
    )

from agents.intake.agent import run_intake_agent
from orchestration.graph import procurement_graph
from tools.shared.llm import get_llm
from tools.dispatch.mailer import send_rfq_email

app = FastAPI(
    title="Kraya — AI Agent Microservice",
    description="Python AI/ML service for quote parsing, XGBoost risk evaluation, and SHAP feature attributions.",
    version="1.0.0"
)

# Register the Evaluation Agent router
if evaluation_router is not None:
    app.include_router(evaluation_router)


class ProcurementWorkflowRequest(BaseModel):
    user_input: str = Field(min_length=1, max_length=12000)
    suppliers: list[dict[str, Any]] = Field(default_factory=list)


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    suppliers: list[dict[str, Any]] = Field(default_factory=list)
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)


class DispatchRFQPayload(BaseModel):
    recipient_email: str
    subject: str
    body: str
    rfq_id: str | None = None
    supplier_name: str | None = None
    contact_name: str | None = None


class NegotiationWorkflowPayload(BaseModel):
    supplier_name: str = "Supplier"
    supplier_email: str = ""
    incoming_message: str
    thread_history: list[dict[str, Any]] = Field(default_factory=list)


PROGRESS_STAGES = [
    "Requirement Analysis",
    "Supplier Discovery",
    "Quote Collection",
    "Evaluation & Comparison",
    "Recommendation"
]


@app.post("/workflows/procurement")
async def run_procurement_workflow(request: ProcurementWorkflowRequest):
    try:
        suppliers = request.suppliers
        if not suppliers:
            from tools.supplier.supplier_repository import SupplierRepository
            suppliers = [s.model_dump(mode="json") for s in SupplierRepository.get_all_suppliers(active_only=True)]

        result = procurement_graph.invoke({
            "user_input": request.user_input,
            "supplier_candidates_input": suppliers,
            "errors": [],
        })
        return result
    except Exception as error:
        raise HTTPException(status_code=502, detail="Procurement workflow execution failed") from error


@app.post("/chat")
async def handle_agent_chat(request: AgentChatRequest):
    message = request.message.strip()
    suppliers = request.suppliers
    lower = message.lower()

    # Detect procurement requirement intent
    procurement_keywords = [
        "need", "procure", "buy", "purchase", "order", "laptop", "laptops",
        "budget", "quotation", "quote", "rfq", "vendor", "hardware", "software",
        "delivery", "specs", "units", "quantity", "requirement"
    ]
    is_procurement_intent = any(kw in lower for kw in procurement_keywords) and len(message.split()) >= 3

    if is_procurement_intent:
        try:
            workflow_res = procurement_graph.invoke({
                "user_input": message,
                "supplier_candidates_input": suppliers,
                "errors": [],
            })

            workflow_status = workflow_res.get("workflow_status", "validated")
            req = workflow_res.get("requirement") or workflow_res.get("requirement_draft") or {}
            clarification_questions = workflow_res.get("clarification_questions", [])
            decisions = workflow_res.get("supplier_eligibility_results", [])
            drafts = workflow_res.get("rfq_drafts", [])

            # Build conversational reply based on real LangGraph execution
            if workflow_status == "needs_clarification" and clarification_questions:
                reply = "I've started analyzing your requirement, but I need a few more details to proceed:\n\n"
                for q in clarification_questions:
                    reply += f"• {q}\n"
                reply += "\nPlease provide these details so I can match suitable suppliers."
                stage_idx = 0
                steps = [
                    {"label": "Extract and validate your requirements", "status": "current", "done": False},
                    {"label": "Discover and shortlist suitable suppliers", "status": "pending", "done": False},
                    {"label": "Collect quotes and compare options", "status": "pending", "done": False},
                    {"label": "Evaluate suppliers (price, delivery, reliability, risk)", "status": "pending", "done": False},
                    {"label": "Share my recommendation for your approval", "status": "pending", "done": False}
                ]
            elif workflow_status == "no_eligible_suppliers":
                prod = req.get("product_service", "requested item")
                qty = req.get("quantity")
                budget = req.get("budget")
                curr = req.get("currency", "INR")
                loc = req.get("delivery_location")

                reply = f"I've validated your requirement for **{f'{int(qty)} ' if qty else ''}{prod}**"
                if budget:
                    reply += f" with budget **{curr} {budget:,.0f}**"
                if loc:
                    reply += f" to **{loc}**"
                reply += ".\n\n"

                if suppliers:
                    reply += f"I evaluated **{len(suppliers)} suppliers** in your directory, but none currently match the category and delivery constraints for {prod}.\n\n"
                    reply += "• **Next Step:** You can onboard a new supplier in this category or adjust delivery requirements."
                else:
                    reply += "Your supplier directory currently has no active suppliers registered. Please add suppliers or broaden specifications."

                stage_idx = 1
                steps = [
                    {"label": "Extract and validate your requirements", "status": "done", "done": True},
                    {"label": "Discover and shortlist suitable suppliers", "status": "current", "done": False},
                    {"label": "Collect quotes and compare options", "status": "pending", "done": False},
                    {"label": "Evaluate suppliers (price, delivery, reliability, risk)", "status": "pending", "done": False},
                    {"label": "Share my recommendation for your approval", "status": "pending", "done": False}
                ]
            elif drafts:
                reply = f"Great news! I've drafted **{len(drafts)} RFQs** for qualified suppliers matching your requirement.\n\n"
                for d in drafts[:3]:
                    sname = d.get("supplier", {}).get("name", "Vendor")
                    subj = d.get("email_subject", "RFQ Request")
                    reply += f"• **{sname}**: {subj}\n"
                reply += "\nThese are ready for your review and automated dispatch."
                stage_idx = 2
                steps = [
                    {"label": "Extract and validate your requirements", "status": "done", "done": True},
                    {"label": "Discover and shortlist suitable suppliers", "status": "done", "done": True},
                    {"label": "Collect quotes and compare options", "status": "current", "done": False},
                    {"label": "Evaluate suppliers (price, delivery, reliability, risk)", "status": "pending", "done": False},
                    {"label": "Share my recommendation for your approval", "status": "pending", "done": False}
                ]
            else:
                reply = "Got it! I've extracted your requirement and initiated the autonomous procurement workflow.\n\nHere's the plan:"
                stage_idx = 1
                steps = [
                    {"label": "Extract and validate your requirements", "status": "done", "done": True},
                    {"label": "Discover and shortlist suitable suppliers", "status": "current", "done": False},
                    {"label": "Collect quotes and compare options", "status": "pending", "done": False},
                    {"label": "Evaluate suppliers (price, delivery, reliability, risk)", "status": "pending", "done": False},
                    {"label": "Share my recommendation for your approval", "status": "pending", "done": False}
                ]

            return {
                "reply": reply,
                "followUp": "I'll keep you updated in real time as the agents advance through the pipeline.",
                "steps": steps,
                "procurementProgress": {
                    "currentStage": PROGRESS_STAGES[min(stage_idx, len(PROGRESS_STAGES) - 1)],
                    "currentStageIndex": stage_idx,
                    "stages": PROGRESS_STAGES
                },
                "workflow_result": workflow_res
            }
        except Exception as err:
            logging.getLogger(__name__).warning("Procurement graph error in /chat: %s", err)

    # General / conversational query using Gemini LLM directly with live supplier & platform context
    try:
        llm = get_llm(temperature=0.2)
        supplier_summary = ""
        if suppliers:
            supplier_summary = f"There are {len(suppliers)} active suppliers in the tenant catalog: " + ", ".join(
                f"{s.get('name', 'Unknown')} ({s.get('country_code', 'IN')}, categories: {', '.join(s.get('categories', []))})"
                for s in suppliers[:8]
            )
        else:
            supplier_summary = "No suppliers currently registered in the database."

        system_prompt = (
            "You are Kraya Agent, an autonomous enterprise AI procurement co-pilot for Kraya platform.\n"
            "You help procurement managers validate requirements, search suppliers, compare quotes, "
            "explain TreeSHAP risk factors, draft RFQs, and track pipeline progress.\n"
            "Be professional, concise, direct, and actionable. Format responses with clean markdown (bold, bullet points).\n"
            f"Current Context: {supplier_summary}\n\n"
            f"User says: {message}\n"
            "Answer directly and helpfully:"
        )

        llm_response = llm.invoke(system_prompt)
        # Extract text from response
        content = llm_response.content
        if isinstance(content, list):
            reply_text = "".join(item.get("text", "") if isinstance(item, dict) else str(item) for item in content)
        else:
            reply_text = str(content)

        # Determine suitable stage
        if "supplier" in lower or "vendor" in lower:
            stage_idx = 1
        elif "quote" in lower or "price" in lower or "compare" in lower:
            stage_idx = 2
        elif "evaluat" in lower or "risk" in lower or "shap" in lower:
            stage_idx = 3
        elif "status" in lower or "progress" in lower:
            stage_idx = 1
        else:
            stage_idx = 0

        steps = [
            {"label": "Extract and validate your requirements", "status": "done" if stage_idx > 0 else "current", "done": stage_idx > 0},
            {"label": "Discover and shortlist suitable suppliers", "status": "done" if stage_idx > 1 else ("current" if stage_idx == 1 else "pending"), "done": stage_idx > 1},
            {"label": "Collect quotes and compare options", "status": "done" if stage_idx > 2 else ("current" if stage_idx == 2 else "pending"), "done": stage_idx > 2},
            {"label": "Evaluate suppliers (price, delivery, reliability, risk)", "status": "done" if stage_idx > 3 else ("current" if stage_idx == 3 else "pending"), "done": stage_idx > 3},
            {"label": "Share my recommendation for your approval", "status": "current" if stage_idx == 4 else "pending", "done": False}
        ]

        return {
            "reply": reply_text.strip(),
            "steps": steps,
            "procurementProgress": {
                "currentStage": PROGRESS_STAGES[min(stage_idx, len(PROGRESS_STAGES) - 1)],
                "currentStageIndex": stage_idx,
                "stages": PROGRESS_STAGES
            }
        }

    except Exception as err:
        logging.getLogger(__name__).error("Gemini chat fallback error: %s", err)
        return {
            "reply": f"I received your message: \"{message}\". How would you like me to assist with your procurement requirements or suppliers?",
            "steps": [
                {"label": "Extract and validate your requirements", "status": "current", "done": False},
                {"label": "Discover and shortlist suitable suppliers", "status": "pending", "done": False},
                {"label": "Collect quotes and compare options", "status": "pending", "done": False},
                {"label": "Evaluate suppliers (price, delivery, reliability, risk)", "status": "pending", "done": False},
                {"label": "Share my recommendation for your approval", "status": "pending", "done": False}
            ],
            "procurementProgress": {
                "currentStage": "Requirement Analysis",
                "currentStageIndex": 0,
                "stages": PROGRESS_STAGES
            }
        }


@app.post("/dispatch/send-rfq")
async def dispatch_rfq_endpoint(payload: DispatchRFQPayload):
    try:
        result = send_rfq_email(
            recipient=payload.recipient_email,
            subject=payload.subject,
            body=payload.body,
            rfq_id=payload.rfq_id,
            supplier_name=payload.supplier_name,
            contact_name=payload.contact_name
        )
        return result
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/workflows/negotiate")
async def handle_negotiation(payload: NegotiationWorkflowPayload):
    supplier_name = payload.supplier_name or "Supplier"
    incoming = payload.incoming_message.strip()
    is_acceptance = any(w in incoming.lower() for w in ["accept", "agree", "confirm", "deal", "proceed with"])

    if is_acceptance:
        return {
            "intent": "acceptance",
            "recommended_stage": "APPROVAL",
            "strategy": f"{supplier_name} confirmed agreed pricing and delivery terms. Preparing Purchase Order.",
            "reply_subject": f"Agreement Confirmation: Purchase Order Preparation - Kraya",
            "reply_body": (
                f"Dear {supplier_name},\n\n"
                f"Thank you for confirming the agreed terms. Our enterprise procurement team has approved "
                f"this proposal, and we have initialized the formal Purchase Order (PO) creation workflow.\n\n"
                f"We will transmit the official PO documentation shortly for order execution.\n\n"
                f"Best regards,\nKraya Autonomous Procurement Agent"
            ),
            "extracted_quote": {"status": "agreed"}
        }

    price_match = re.search(r'(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)', incoming, re.IGNORECASE)
    quoted_price = price_match.group(0) if price_match else "your quoted price"

    try:
        llm = get_llm()
        prompt = (
            f"You are the Kraya AI Autonomous Procurement & Negotiation Agent representing a corporate enterprise buyer.\n"
            f"Supplier Name: {supplier_name}\n"
            f"Supplier Email Received:\n\"{incoming}\"\n\n"
            f"Task: Draft a professional B2B email response negotiating a 5% volume discount, Net-30 payment terms, and 3-year warranty.\n"
            f"Format response as JSON: {{\"strategy\": \"...\", \"reply_subject\": \"...\", \"reply_body\": \"...\"}}"
        )
        response = llm.invoke(prompt)
        raw_content = response.content if hasattr(response, "content") else str(response)
        text = raw_content if isinstance(raw_content, str) else "\n".join(str(part) for part in raw_content)
        clean = text.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()
        data = json.loads(clean)
        return {
            "intent": "quote",
            "recommended_stage": "NEGOTIATION",
            "strategy": data.get("strategy", f"Analyzed quotation from {supplier_name}. Proposed 5% volume discount with Net-30 terms."),
            "reply_subject": data.get("reply_subject", f"RE: Quotation Review & Commercial Terms - Kraya"),
            "reply_body": data.get("reply_body", ""),
            "extracted_quote": {"price": quoted_price}
        }
    except Exception as e:
        logging.getLogger(__name__).warning("LLM negotiation generation fell back to deterministic template: %s", e)
        return {
            "intent": "quote",
            "recommended_stage": "NEGOTIATION",
            "strategy": f"Quotation from {supplier_name} analyzed. Proposed 5% enterprise discount with Net-30 payment terms.",
            "reply_subject": f"RE: Quotation Evaluation & Commercial Terms - Kraya",
            "reply_body": (
                f"Dear {supplier_name},\n\n"
                f"Thank you for your prompt quotation regarding our requirement. "
                f"We have reviewed the specifications and delivery timeline, which meet our enterprise standards.\n\n"
                f"Our approved budget for immediate execution is capped with a target 5% adjustment on {quoted_price}, "
                f"subject to standard Net-30 payment terms and the 3-year manufacturer warranty. "
                f"If you can accommodate these terms, we will immediately issue the official Purchase Order.\n\n"
                f"We look forward to your confirmation.\n\n"
                f"Best regards,\nKraya Autonomous Procurement Agent"
            ),
            "extracted_quote": {"price": quoted_price}
        }


class PollInboxPayload(BaseModel):
    procurement_request_id: str
    supplier_email: str | None = None
    supplier_name: str = "TechNova Solutions"
    incoming_message: str | None = None
    auto_reply: bool = True


class ConfigureGmailPayload(BaseModel):
    email: str
    app_password: str


@app.get("/inbox/gmail-status")
async def get_gmail_status_endpoint():
    from tools.inbox.gmail_imap_connector import check_gmail_connection
    return check_gmail_connection()


@app.post("/inbox/configure-gmail")
async def configure_gmail_endpoint(payload: ConfigureGmailPayload):
    from tools.inbox.gmail_imap_connector import update_gmail_credentials, check_gmail_connection
    update_gmail_credentials(payload.email, payload.app_password)
    status = check_gmail_connection()
    return status


@app.post("/inbox/poll-and-process")
async def poll_inbox_and_process(payload: PollInboxPayload):
    try:
        from services.inbox_service import poll_and_process_supplier_emails
        res = poll_and_process_supplier_emails(
            procurement_request_id=payload.procurement_request_id,
            supplier_email=payload.supplier_email,
            incoming_message=payload.incoming_message,
            supplier_name=payload.supplier_name,
            auto_reply=payload.auto_reply
        )
        return res
    except Exception as error:
        logging.getLogger(__name__).error("Inbox poll and process error: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "UP", "service": "kraya-agents"}


def main():
    print("\n========== KRAYA INTAKE AGENT ==========")
    user_input = input("Enter your procurement requirement:\n> ")
    existing_requirement = None
    while True:
        result = run_intake_agent(
            user_input=user_input,
            existing_requirement=existing_requirement
        )
        print("\n========== INTAKE RESULT ==========")
        if result["status"] == "validated":
            print("Requirement successfully validated.")
            print("\nFinal Requirement:\n", result["requirement"])
            break
        elif result["status"] == "needs_clarification":
            print("Additional information required.\n")
            existing_requirement = result["requirement_draft"]
            for question in result["clarification_questions"]:
                print("-", question)
            user_input = input("\nYour response:\n> ")
        else:
            print("Intake failed:", result["errors"])
            break


if __name__ == "__main__":
    main()
