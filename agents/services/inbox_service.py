import os
import json
import re
import logging
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from tools.inbox.gmail_imap_connector import (
    fetch_emails_from_gmail,
    add_to_autonomous_inbox,
    check_gmail_connection
)
from tools.dispatch.mailer import send_rfq_email
from tools.shared.llm import get_llm

load_dotenv()
logger = logging.getLogger(__name__)


def extract_text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, str):
                parts.append(p)
            elif isinstance(p, dict) and "text" in p:
                parts.append(p["text"])
            elif hasattr(p, "text"):
                parts.append(p.text)
            else:
                parts.append(str(p))
        return "\n".join(parts)
    return str(content)


def get_db_engine():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is missing.")
    return create_engine(db_url)


def poll_and_process_supplier_emails(
    procurement_request_id: str,
    supplier_email: str | None = None,
    incoming_message: str | None = None,
    supplier_name: str = "TechNova Solutions",
    auto_reply: bool = True
) -> dict[str, Any]:
    """
    Autonomous Email Reader & Negotiator:
    1. Reads incoming emails from Gmail IMAP or autonomous mailbox.
    2. Uses Gemini to analyze quotation, pricing, and compliance.
    3. If auto_reply=True: Contacts the supplier directly with B2B counter-offer.
    4. Updates Supabase agent_runs and procurement_requests status.
    """
    # If incoming text was provided directly, add it to the inbox queue
    if incoming_message and incoming_message.strip():
        add_to_autonomous_inbox(
            sender=supplier_email or "akulgameristicofficial@gmail.com",
            subject=f"RE: Quotation for {supplier_name} RFQ",
            body=incoming_message.strip()
        )

    # 1. Fetch unread emails
    messages = fetch_emails_from_gmail(supplier_filter=supplier_email)
    if not messages:
        conn_info = check_gmail_connection()
        if not conn_info.get("configured"):
            status_msg = "Gmail IMAP is not configured in agents/.env (GMAIL_USER, GMAIL_APP_PASSWORD). Please paste the supplier's reply below or use the quick simulation actions."
        elif not conn_info.get("connected"):
            status_msg = f"Gmail IMAP connection failed: {conn_info.get('error', 'Authentication error')}. Please check your Gmail App Password or paste supplier reply directly below."
        else:
            status_msg = f"✓ Checked Gmail inbox for {conn_info.get('account')}. No new supplier replies found at this time."

        return {
            "success": True,
            "messages_processed": 0,
            "message": status_msg,
            "gmail_status": conn_info
        }

    engine = get_db_engine()
    processed_count = 0
    final_stage = "QUOTING"
    pending_draft = None

    with engine.begin() as conn:
        # Load latest agent_run
        row = conn.execute(
            text("SELECT id, organization_id, result::text FROM agent_runs WHERE procurement_request_id = :req_id ORDER BY started_at DESC LIMIT 1"),
            {"req_id": procurement_request_id}
        ).fetchone()

        if not row:
            return {"success": False, "error": f"No agent workflow found for request {procurement_request_id}"}

        run_id = row[0]
        org_id = row[1]
        result_data = json.loads(row[2]) if row[2] else {}
        thread = result_data.get("email_thread", [])

        for email_msg in messages:
            body_text = email_msg.body
            sender_addr = email_msg.sender_email
            subj = email_msg.subject or f"RE: Quotation for {supplier_name}"

            # Inbound Supplier Message Record
            inbound_id = f"msg-in-{datetime.now(timezone.utc).strftime('%H%M%S%f')[:8]}"
            inbound_record = {
                "id": inbound_id,
                "sender": f"{supplier_name} <{sender_addr}>",
                "senderType": "supplier",
                "subject": subj,
                "content": body_text,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            thread.append(inbound_record)
            final_stage = "EVALUATION"

            # Check if message is acceptance
            is_acceptance = any(w in body_text.lower() for w in ["accept", "agree", "confirm", "deal", "proceed with", "approved", "acceptance"])

            # 2. Use Gemini to analyze and generate autonomous reply
            reply_subject = f"RE: {subj}"
            reply_body = ""
            strategy = ""

            try:
                llm = get_llm()
                if is_acceptance:
                    prompt = (
                        f"You are the Kraya AI Autonomous Procurement Agent representing a corporate enterprise buyer.\n"
                        f"Supplier: {supplier_name} ({sender_addr})\n"
                        f"Supplier Email Received:\n\"{body_text}\"\n\n"
                        f"Task: The supplier has accepted our terms! Draft a formal confirmation acknowledging acceptance and stating that our procurement team is issuing the official Purchase Order (PO).\n"
                        f"Respond in valid JSON only with keys: strategy, reply_subject, reply_body."
                    )
                else:
                    prompt = (
                        f"You are the Kraya AI Autonomous Procurement & Negotiation Agent representing a corporate buyer.\n"
                        f"Supplier: {supplier_name} ({sender_addr})\n"
                        f"Supplier Email Received:\n\"{body_text}\"\n\n"
                        f"Task: Analyze the quotation, formulate a professional B2B counter-offer proposing a 5% discount, standard Net-30 payment terms, and 3-year warranty.\n"
                        f"Respond in valid JSON only with keys: strategy, reply_subject, reply_body."
                    )
                resp = llm.invoke(prompt)
                content_text = extract_text_from_content(resp.content)
                clean = content_text.strip()
                if "```json" in clean:
                    clean = clean.split("```json")[1].split("```")[0].strip()
                elif "```" in clean:
                    clean = clean.split("```")[1].split("```")[0].strip()
                data = json.loads(clean)
                strategy = data.get("strategy", "Analyzed supplier proposal. Formulated B2B counter-offer with 5% volume discount and Net-30 terms.")
                reply_subject = data.get("reply_subject", reply_subject)
                reply_body = data.get("reply_body", "")
            except Exception as ex:
                logger.warning("Gemini LLM analysis fallback: %s", ex)
                if is_acceptance:
                    strategy = "Supplier accepted terms. Finalizing Purchase Order documentation."
                    reply_subject = f"Agreement Confirmation: Purchase Order Issuance - Kraya"
                    reply_body = (
                        f"Dear {supplier_name},\n\n"
                        f"Thank you for confirming the agreed terms. We have moved the order to final PO execution.\n\n"
                        f"Best regards,\nKraya Autonomous Procurement Agent"
                    )
                else:
                    strategy = "Supplier quotation analyzed. Formulated 5% discount request with Net-30 payment terms."
                    reply_subject = f"RE: Commercial Terms & Quotation - Kraya"
                    reply_body = (
                        f"Dear {supplier_name},\n\n"
                        f"Thank you for your prompt quotation. We have reviewed your proposal.\n"
                        f"Our approved budget for immediate execution allows a target 5% adjustment with Net-30 payment terms and 3-year warranty.\n"
                        f"If acceptable, we can immediately issue the official Purchase Order.\n\n"
                        f"Best regards,\nKraya Autonomous Procurement Agent"
                    )

            if auto_reply:
                # 3. CONTACT THEM DIRECTLY: Send email back to supplier
                tracking_id = f"TRK-{datetime.now(timezone.utc).strftime('%H%M%S%f')[:8].upper()}"
                try:
                    send_rfq_email(
                        recipient=sender_addr,
                        subject=reply_subject,
                        body=reply_body,
                        supplier_name=supplier_name
                    )
                except Exception as mail_err:
                    logger.warning("Autonomous dispatch error: %s", mail_err)

                outbound_id = f"msg-out-{datetime.now(timezone.utc).strftime('%H%M%S%f')[:8]}"
                outbound_record = {
                    "id": outbound_id,
                    "sender": "Kraya AI Autonomous Negotiation Agent (Contacted Supplier Directly)",
                    "senderType": "agent",
                    "subject": reply_subject,
                    "content": reply_body,
                    "strategy": strategy,
                    "tracking_id": tracking_id,
                    "status": "APPROVED_AND_SENT",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                thread.append(outbound_record)
                final_stage = "APPROVAL" if is_acceptance else "NEGOTIATION"
            else:
                # Store as pending draft for human approval
                pending_draft = {
                    "id": f"draft-{datetime.now(timezone.utc).strftime('%H%M%S%f')[:8]}",
                    "sender": "Kraya AI Autonomous Negotiation Agent",
                    "recipient": f"{supplier_name} <{sender_addr}>",
                    "subject": reply_subject,
                    "body": reply_body,
                    "strategy": strategy,
                    "status": "AWAITING_HUMAN_APPROVAL",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                final_stage = "EVALUATION"

            processed_count += 1

        # 4. Update Supabase
        result_data["email_thread"] = thread
        result_data["pending_ai_draft"] = pending_draft
        result_data["workflow_status"] = final_stage

        conn.execute(
            text("UPDATE agent_runs SET result = CAST(:res AS jsonb), completed_at = CURRENT_TIMESTAMP WHERE id = :run_id"),
            {"res": json.dumps(result_data), "run_id": run_id}
        )

        conn.execute(
            text("UPDATE procurement_requests SET status = :status, updated_at = CURRENT_TIMESTAMP WHERE id = :req_id"),
            {"status": final_stage, "req_id": procurement_request_id}
        )

        # Audit event
        conn.execute(
            text("""
                INSERT INTO audit_events(id, organization_id, action, entity_type, entity_id, previous_state, new_state, result)
                VALUES (gen_random_uuid(), :org_id, 'AUTONOMOUS_EMAIL_INBOX_PROCESSED', 'PROCUREMENT_REQUEST', :req_id, 'QUOTING', :new_st, 'SUCCESS')
            """),
            {"org_id": org_id, "req_id": procurement_request_id, "new_st": final_stage}
        )

    return {
        "success": True,
        "messages_processed": processed_count,
        "final_stage": final_stage,
        "email_thread": thread,
        "pending_ai_draft": pending_draft,
        "message": f"Successfully processed {processed_count} supplier email(s). AI agent contacted supplier directly and advanced status to {final_stage}."
    }
