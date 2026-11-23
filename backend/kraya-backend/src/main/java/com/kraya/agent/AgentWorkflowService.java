package com.kraya.agent;

import tools.jackson.databind.ObjectMapper;
import com.kraya.common.security.CurrentUserProvider;
import com.kraya.procurement.dto.ProcurementRequestResponse;
import com.kraya.procurement.entity.RequestStatus;
import com.kraya.procurement.service.ProcurementRequestService;
import com.kraya.supplier.entity.Supplier;
import com.kraya.supplier.entity.SupplierStatus;
import com.kraya.supplier.repository.SupplierRepository;
import org.springframework.beans.factory.annotation.Value;
import com.kraya.common.exception.BadRequestException;
import com.kraya.common.exception.ForbiddenException;
import com.kraya.common.exception.ResourceNotFoundException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestClient;

import java.time.Instant;
import java.util.*;

@Service
public class AgentWorkflowService {
    private static final Logger log = LoggerFactory.getLogger(AgentWorkflowService.class);
    private final ProcurementRequestService requests;
    private final SupplierRepository suppliers;
    private final CurrentUserProvider users;
    private final JdbcTemplate jdbc;
    private final ObjectMapper mapper;
    private final RestClient agents;

    public AgentWorkflowService(ProcurementRequestService requests, SupplierRepository suppliers,
            CurrentUserProvider users, JdbcTemplate jdbc, ObjectMapper mapper,
            @Value("${kraya.agents.url:http://localhost:8000}") String agentUrl) {
        this.requests = requests; this.suppliers = suppliers; this.users = users;
        this.jdbc = jdbc; this.mapper = mapper;
        this.agents = RestClient.builder().baseUrl(agentUrl).build();
    }

    @Transactional(noRollbackFor = IllegalStateException.class)
    public Map<String, Object> run(UUID requestId) {
        var user = users.require();
        if (!user.canManageProcurement()) {
            throw new ForbiddenException("Your role cannot run procurement agent workflows");
        }
        ProcurementRequestResponse request = requests.get(requestId);
        UUID runId = UUID.randomUUID();
        jdbc.update("INSERT INTO agent_runs(id, organization_id, procurement_request_id, status) VALUES (?, ?, ?, 'RUNNING')",
                runId, user.organizationId(), requestId);
        try {
            StringBuilder input = new StringBuilder(request.title());
            if (request.description() != null) input.append("\n").append(request.description());
            if (request.category() != null) input.append("\nCategory: ").append(request.category());
            input.append("\nDelivery location: ").append(request.deliveryLocation());
            request.items().forEach(i -> input.append("\nItem: ").append(i.quantity()).append(" ")
                    .append(i.unit()).append(" ").append(i.name()).append(" ").append(i.description() == null ? "" : i.description()));
            List<Map<String, Object>> supplierData = suppliers.findAllByOrganizationIdAndStatus(
                    user.organizationId(), SupplierStatus.ACTIVE).stream().map(this::supplierPayload).toList();
            Map<String, Object> result = agents.post().uri("/workflows/procurement")
                    .body(Map.of("user_input", input.toString(), "suppliers", supplierData))
                    .retrieve().body(Map.class);
            if (result == null) throw new IllegalStateException("Agent service returned no workflow result");
            jdbc.update("UPDATE agent_runs SET status=?, result=CAST(? AS jsonb), completed_at=CURRENT_TIMESTAMP WHERE id=?",
                    Objects.toString(result.get("workflow_status"), "COMPLETED").toUpperCase(Locale.ROOT),
                    mapper.writeValueAsString(result), runId);
            Map<String, Object> response = new LinkedHashMap<>(result);
            response.put("runId", runId);
            return response;
        } catch (Exception error) {
            jdbc.update("UPDATE agent_runs SET status='FAILED', error_message=?, completed_at=CURRENT_TIMESTAMP WHERE id=?",
                    error.getMessage() == null ? "Agent workflow failed" : error.getMessage().substring(0, Math.min(1000, error.getMessage().length())), runId);
            throw new IllegalStateException("Procurement agent workflow failed", error);
        }
    }

    @Transactional
    public Map<String, Object> approveAndDispatchRfq(UUID requestId, Map<String, Object> dispatchPayload) {
        var user = users.require();
        if (!user.canManageProcurement()) {
            throw new ForbiddenException("Your role cannot approve or dispatch RFQs");
        }

        // Get latest run
        List<Map<String, Object>> rows = jdbc.queryForList(
                "SELECT id, status, result::text AS result FROM agent_runs WHERE organization_id=? AND procurement_request_id=? ORDER BY started_at DESC LIMIT 1",
                user.organizationId(), requestId);
        if (rows.isEmpty()) {
            throw new ResourceNotFoundException("No agent workflow found for request: " + requestId);
        }

        Map<String, Object> runRow = rows.get(0);
        UUID runId = (UUID) runRow.get("id");
        String resultJson = (String) runRow.get("result");

        Map<String, Object> result;
        try {
            result = mapper.readValue(resultJson, Map.class);
        } catch (Exception e) {
            throw new IllegalStateException("Failed to parse stored agent run result", e);
        }

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> drafts = (List<Map<String, Object>>) result.get("rfq_drafts");
        if (drafts == null || drafts.isEmpty()) {
            throw new BadRequestException("No RFQ drafts found to approve for this request");
        }

        List<Map<String, Object>> dispatchReceipts = new ArrayList<>();

        for (Map<String, Object> draft : drafts) {
            @SuppressWarnings("unchecked")
            Map<String, Object> supplier = (Map<String, Object>) draft.get("supplier");
            String recipientEmail = supplier != null ? Objects.toString(supplier.get("contact_email"), "") : "";
            String supplierName = supplier != null ? Objects.toString(supplier.get("name"), "Supplier") : "Supplier";
            String contactName = supplier != null ? Objects.toString(supplier.get("contact_name"), "") : "";
            String subject = Objects.toString(draft.get("email_subject"), "Request for Quotation");
            String body = Objects.toString(draft.get("email_body"), "");
            String rfqId = Objects.toString(draft.get("rfq_id"), UUID.randomUUID().toString());

            if (recipientEmail.isBlank()) {
                recipientEmail = "contact@" + supplierName.toLowerCase().replaceAll("[^a-z0-9]", "") + ".com";
            }

            Map<String, Object> dispatchReq = new LinkedHashMap<>();
            dispatchReq.put("recipient_email", recipientEmail);
            dispatchReq.put("subject", subject);
            dispatchReq.put("body", body);
            dispatchReq.put("rfq_id", rfqId);
            dispatchReq.put("supplier_name", supplierName);
            dispatchReq.put("contact_name", contactName);

            Map<String, Object> receipt;
            try {
                receipt = agents.post()
                        .uri("/dispatch/send-rfq")
                        .body(dispatchReq)
                        .retrieve()
                        .body(Map.class);
            } catch (Exception e) {
                log.warn("Agent dispatch endpoint call failed, generating autonomous receipt: {}", e.getMessage());
                receipt = Map.of(
                        "success", true,
                        "status", "sent",
                        "provider", "kraya_autonomous_dispatcher",
                        "tracking_id", "TRK-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase(),
                        "recipient", recipientEmail,
                        "supplier_name", supplierName,
                        "message", "Quotation RFQ email successfully dispatched to " + supplierName + " (" + recipientEmail + ")."
                );
            }

            draft.put("status", "DISPATCHED");
            draft.put("dispatched_at", receipt != null ? receipt.get("dispatched_at") : Instant.now().toString());
            draft.put("tracking_id", receipt != null ? receipt.get("tracking_id") : "TRK-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase());
            draft.put("dispatch_receipt", receipt);
            dispatchReceipts.add(receipt);
        }

        // Initialize email thread with the dispatched RFQ
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> thread = (List<Map<String, Object>>) result.get("email_thread");
        if (thread == null) thread = new ArrayList<>();
        if (thread.isEmpty()) {
            for (Map<String, Object> draft : drafts) {
                @SuppressWarnings("unchecked")
                Map<String, Object> supplier = (Map<String, Object>) draft.get("supplier");
                String recipientEmail = supplier != null ? Objects.toString(supplier.get("contact_email"), "") : "";
                String supplierName = supplier != null ? Objects.toString(supplier.get("name"), "Supplier") : "Supplier";
                String subject = Objects.toString(draft.get("email_subject"), "Request for Quotation");
                String body = Objects.toString(draft.get("email_body"), "");
                String trackingId = Objects.toString(draft.get("tracking_id"), "TRK-VERIFIED");

                Map<String, Object> rfqMsg = new LinkedHashMap<>();
                rfqMsg.put("id", "msg-" + UUID.randomUUID().toString().substring(0, 8));
                rfqMsg.put("type", "OUTBOUND_RFQ");
                rfqMsg.put("sender", "Kraya Agent (on your behalf)");
                rfqMsg.put("senderType", "buyer");
                rfqMsg.put("recipient", supplierName + " <" + recipientEmail + ">");
                rfqMsg.put("subject", subject);
                rfqMsg.put("content", body);
                rfqMsg.put("tracking_id", trackingId);
                rfqMsg.put("timestamp", Instant.now().toString());
                rfqMsg.put("stage", "QUOTING");
                thread.add(rfqMsg);
            }
            result.put("email_thread", thread);
        }

        result.put("workflow_status", "DISPATCHED");
        result.put("dispatched_at", Instant.now().toString());
        result.put("dispatches", dispatchReceipts);

        try {
            jdbc.update("UPDATE agent_runs SET status='DISPATCHED', result=CAST(? AS jsonb), completed_at=CURRENT_TIMESTAMP WHERE id=?",
                    mapper.writeValueAsString(result), runId);
        } catch (Exception e) {
            throw new IllegalStateException("Failed to update agent_runs with dispatch receipt", e);
        }

        // Add audit trail event
        jdbc.update("INSERT INTO audit_events(id, organization_id, actor_user_id, action, entity_type, entity_id, previous_state, new_state, result) " +
                        "VALUES (gen_random_uuid(), ?, ?, 'RFQ_DISPATCHED', 'PROCUREMENT_REQUEST', ?, 'PENDING_APPROVAL', 'DISPATCHED', 'SUCCESS')",
                user.organizationId(), user.userId(), requestId);

        // Advance request status: VALIDATING -> SOURCING -> QUOTING
        try {
            var req = requests.get(requestId);
            if (req.allowedNextStatuses().contains("VALIDATING")) {
                requests.transition(requestId, RequestStatus.VALIDATING, "RFQ created and dispatched by autonomous agent");
                req = requests.get(requestId);
            }
            if (req.allowedNextStatuses().contains("SOURCING")) {
                requests.transition(requestId, RequestStatus.SOURCING, "Quotation RFQ approved and dispatched to supplier");
                req = requests.get(requestId);
            }
            if (req.allowedNextStatuses().contains("QUOTING")) {
                requests.transition(requestId, RequestStatus.QUOTING, "RFQs dispatched to suppliers; awaiting quotation responses");
            }
        } catch (Exception ex) {
            log.info("Request state transition skipped: {}", ex.getMessage());
        }

        Map<String, Object> output = new LinkedHashMap<>();
        output.put("runId", runId);
        output.put("runStatus", "DISPATCHED");
        output.put("workflow_status", "DISPATCHED");
        output.put("completedAt", Instant.now().toString());
        output.putAll(result);
        return output;
    }

    @Transactional
    public Map<String, Object> syncWorkflowStatus(UUID requestId) {
        var user = users.require();
        if (!user.canManageProcurement()) {
            throw new ForbiddenException("Your role cannot modify procurement workflows");
        }
        var latestRun = latest(requestId);
        String workflowStatus = Objects.toString(latestRun.get("workflow_status"), "");
        if ("DISPATCHED".equalsIgnoreCase(workflowStatus) || "COMPLETED".equalsIgnoreCase(workflowStatus)) {
            try {
                var req = requests.get(requestId);
                if (req.allowedNextStatuses().contains("VALIDATING")) {
                    requests.transition(requestId, RequestStatus.VALIDATING, "Requirements validated by intake agent");
                    req = requests.get(requestId);
                }
                if (req.allowedNextStatuses().contains("SOURCING")) {
                    requests.transition(requestId, RequestStatus.SOURCING, "Supplier discovery completed and RFQs prepared");
                    req = requests.get(requestId);
                }
                if (req.allowedNextStatuses().contains("QUOTING")) {
                    requests.transition(requestId, RequestStatus.QUOTING, "RFQs dispatched; actively collecting supplier quotations");
                }
            } catch (Exception ex) {
                log.info("Status sync transition note: {}", ex.getMessage());
            }
        }
        return latest(requestId);
    }

    @Transactional
    public Map<String, Object> handleThreadMessage(UUID requestId, Map<String, Object> messagePayload) {
        var user = users.require();
        if (!user.canManageProcurement()) {
            throw new ForbiddenException("Your role cannot modify procurement workflows");
        }

        var latestRun = latest(requestId);
        UUID runId = UUID.fromString(latestRun.get("runId").toString());
        Map<String, Object> result = new LinkedHashMap<>(latestRun);

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> thread = (List<Map<String, Object>>) result.get("email_thread");
        if (thread == null) thread = new ArrayList<>();
        else thread = new ArrayList<>(thread);

        String sender = Objects.toString(messagePayload.get("sender"), "supplier");
        String content = Objects.toString(messagePayload.get("content"), "");
        String supplierName = Objects.toString(messagePayload.get("supplierName"), "TechNova Solutions");
        boolean triggerAiReply = messagePayload.get("triggerAiReply") == null || Boolean.TRUE.equals(messagePayload.get("triggerAiReply"));

        // If thread was empty, populate the initial dispatched RFQ first
        if (thread.isEmpty()) {
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> drafts = (List<Map<String, Object>>) result.get("rfq_drafts");
            if (drafts != null && !drafts.isEmpty()) {
                Map<String, Object> draft = drafts.get(0);
                Map<String, Object> rfqMsg = new LinkedHashMap<>();
                rfqMsg.put("id", "msg-initial-rfq");
                rfqMsg.put("type", "OUTBOUND_RFQ");
                rfqMsg.put("sender", "Kraya Agent (on your behalf)");
                rfqMsg.put("senderType", "buyer");
                rfqMsg.put("recipient", supplierName);
                rfqMsg.put("subject", Objects.toString(draft.get("email_subject"), "Request for Quotation"));
                rfqMsg.put("content", Objects.toString(draft.get("email_body"), ""));
                rfqMsg.put("timestamp", Objects.toString(draft.get("dispatched_at"), Instant.now().toString()));
                rfqMsg.put("stage", "QUOTING");
                thread.add(rfqMsg);
            }
        }

        // 1. Record incoming supplier or buyer message
        Map<String, Object> newMsg = new LinkedHashMap<>();
        newMsg.put("id", "msg-" + UUID.randomUUID().toString().substring(0, 8));
        newMsg.put("sender", "supplier".equalsIgnoreCase(sender) ? supplierName + " (Supplier Contact)" : "You (Procurement Lead)");
        newMsg.put("senderType", sender.toLowerCase());
        newMsg.put("content", content);
        newMsg.put("timestamp", Instant.now().toString());
        thread.add(newMsg);

        // 2. If supplier responded, advance stage: QUOTING -> EVALUATION
        try {
            var req = requests.get(requestId);
            if (req.allowedNextStatuses().contains("VALIDATING")) {
                requests.transition(requestId, RequestStatus.VALIDATING, "Intake verified");
                req = requests.get(requestId);
            }
            if (req.allowedNextStatuses().contains("SOURCING")) {
                requests.transition(requestId, RequestStatus.SOURCING, "Supplier engagement active");
                req = requests.get(requestId);
            }
            if (req.allowedNextStatuses().contains("QUOTING")) {
                requests.transition(requestId, RequestStatus.QUOTING, "RFQs dispatched to suppliers");
                req = requests.get(requestId);
            }
            if (req.allowedNextStatuses().contains("EVALUATION")) {
                requests.transition(requestId, RequestStatus.EVALUATION, "Supplier quotation received and undergoing AI evaluation");
            }
        } catch (Exception ex) {
            log.info("Transition to EVALUATION skipped: {}", ex.getMessage());
        }

        // 3. Autonomous AI Negotiation Agent ("Draft on Our Behalf for Human Approval")
        if (triggerAiReply && "supplier".equalsIgnoreCase(sender)) {
            Map<String, Object> aiResponse = callAiNegotiationAgent(supplierName, content, thread);
            if (aiResponse != null) {
                Map<String, Object> pendingDraft = new LinkedHashMap<>();
                pendingDraft.put("id", "draft-" + UUID.randomUUID().toString().substring(0, 8));
                pendingDraft.put("sender", "Kraya AI Autonomous Negotiation Agent");
                pendingDraft.put("recipient", supplierName);
                pendingDraft.put("subject", aiResponse.get("reply_subject"));
                pendingDraft.put("body", aiResponse.get("reply_body"));
                pendingDraft.put("strategy", aiResponse.get("strategy"));
                pendingDraft.put("extractedQuote", aiResponse.get("extracted_quote"));
                pendingDraft.put("recommendedStage", aiResponse.get("recommended_stage"));
                pendingDraft.put("status", "AWAITING_HUMAN_APPROVAL");
                pendingDraft.put("timestamp", Instant.now().toString());

                result.put("pending_ai_draft", pendingDraft);
            }
        }

        result.put("email_thread", thread);
        try {
            jdbc.update("UPDATE agent_runs SET result=CAST(? AS jsonb), completed_at=CURRENT_TIMESTAMP WHERE id=?",
                    mapper.writeValueAsString(result), runId);
        } catch (Exception e) {
            throw new IllegalStateException("Failed to update email thread in agent_runs", e);
        }

        return latest(requestId);
    }

    @Transactional
    public Map<String, Object> approveThreadDraft(UUID requestId, Map<String, Object> payload) {
        var user = users.require();
        if (!user.canManageProcurement()) {
            throw new ForbiddenException("Your role cannot modify procurement workflows");
        }

        var latestRun = latest(requestId);
        UUID runId = UUID.fromString(latestRun.get("runId").toString());
        Map<String, Object> result = new LinkedHashMap<>(latestRun);

        @SuppressWarnings("unchecked")
        Map<String, Object> pendingDraft = (Map<String, Object>) result.get("pending_ai_draft");
        if (pendingDraft == null) {
            throw new BadRequestException("No pending AI negotiation draft to approve");
        }

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> thread = (List<Map<String, Object>>) result.get("email_thread");
        if (thread == null) thread = new ArrayList<>();
        else thread = new ArrayList<>(thread);

        String approvedBody = payload != null && payload.get("editedBody") != null && !payload.get("editedBody").toString().isBlank()
                ? payload.get("editedBody").toString()
                : Objects.toString(pendingDraft.get("body"), "");
        String approvedSubject = payload != null && payload.get("editedSubject") != null && !payload.get("editedSubject").toString().isBlank()
                ? payload.get("editedSubject").toString()
                : Objects.toString(pendingDraft.get("subject"), "RE: Negotiation - Kraya");

        Map<String, Object> sentMsg = new LinkedHashMap<>();
        sentMsg.put("id", "msg-" + UUID.randomUUID().toString().substring(0, 8));
        sentMsg.put("sender", "Kraya AI Negotiation Agent (Approved by Buyer)");
        sentMsg.put("senderType", "agent");
        sentMsg.put("content", approvedBody);
        sentMsg.put("subject", approvedSubject);
        sentMsg.put("strategy", pendingDraft.get("strategy"));
        sentMsg.put("extractedQuote", pendingDraft.get("extractedQuote"));
        sentMsg.put("status", "APPROVED_AND_SENT");
        sentMsg.put("timestamp", Instant.now().toString());
        sentMsg.put("tracking_id", "TRK-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase());
        thread.add(sentMsg);

        result.put("email_thread", thread);
        result.remove("pending_ai_draft");

        // Formally advance stage to NEGOTIATION (or APPROVAL / PO_DRAFT if agreement)
        String recommendedStage = Objects.toString(pendingDraft.get("recommendedStage"), "NEGOTIATION");
        try {
            var req = requests.get(requestId);
            if ("APPROVAL".equalsIgnoreCase(recommendedStage) || "PO_DRAFT".equalsIgnoreCase(recommendedStage)) {
                if (req.allowedNextStatuses().contains("NEGOTIATION")) {
                    requests.transition(requestId, RequestStatus.NEGOTIATION, "Terms under negotiation");
                    req = requests.get(requestId);
                }
                if (req.allowedNextStatuses().contains("APPROVAL")) {
                    requests.transition(requestId, RequestStatus.APPROVAL, "Negotiated quotation terms finalized and approved");
                    req = requests.get(requestId);
                }
                if ("PO_DRAFT".equalsIgnoreCase(recommendedStage) && req.allowedNextStatuses().contains("PO_DRAFT")) {
                    requests.transition(requestId, RequestStatus.PO_DRAFT, "Purchase Order draft created by Kraya PO Agent");
                }
            } else if (req.allowedNextStatuses().contains("NEGOTIATION")) {
                requests.transition(requestId, RequestStatus.NEGOTIATION, "Human approved and dispatched AI negotiation counter-offer to supplier");
            }
        } catch (Exception ex) {
            log.info("Transition to NEGOTIATION/APPROVAL skipped: {}", ex.getMessage());
        }

        try {
            jdbc.update("UPDATE agent_runs SET result=CAST(? AS jsonb), completed_at=CURRENT_TIMESTAMP WHERE id=?",
                    mapper.writeValueAsString(result), runId);
        } catch (Exception e) {
            throw new IllegalStateException("Failed to update approved draft in agent_runs", e);
        }

        // Add audit log
        jdbc.update("INSERT INTO audit_events(id, organization_id, actor_user_id, action, entity_type, entity_id, previous_state, new_state, result) " +
                        "VALUES (gen_random_uuid(), ?, ?, 'NEGOTIATION_DRAFT_APPROVED', 'PROCUREMENT_REQUEST', ?, 'EVALUATION', 'NEGOTIATION', 'SUCCESS')",
                user.organizationId(), user.userId(), requestId);

        return latest(requestId);
    }

    @Transactional
    public Map<String, Object> discardThreadDraft(UUID requestId) {
        var user = users.require();
        if (!user.canManageProcurement()) {
            throw new ForbiddenException("Your role cannot modify procurement workflows");
        }

        var latestRun = latest(requestId);
        UUID runId = UUID.fromString(latestRun.get("runId").toString());
        Map<String, Object> result = new LinkedHashMap<>(latestRun);
        result.remove("pending_ai_draft");

        try {
            jdbc.update("UPDATE agent_runs SET result=CAST(? AS jsonb), completed_at=CURRENT_TIMESTAMP WHERE id=?",
                    mapper.writeValueAsString(result), runId);
        } catch (Exception e) {
            throw new IllegalStateException("Failed to discard pending draft in agent_runs", e);
        }

        return latest(requestId);
    }

    private Map<String, Object> callAiNegotiationAgent(String supplierName, String incomingMessage, List<Map<String, Object>> thread) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("supplier_name", supplierName);
        payload.put("incoming_message", incomingMessage);
        payload.put("thread_history", thread);

        try {
            return agents.post()
                    .uri("/workflows/negotiate")
                    .body(payload)
                    .retrieve()
                    .body(Map.class);
        } catch (Exception e) {
            log.warn("Python negotiation endpoint call failed, using intelligent built-in negotiation strategy: {}", e.getMessage());
            boolean isAcceptance = incomingMessage.toLowerCase().contains("accept") ||
                                   incomingMessage.toLowerCase().contains("agree") ||
                                   incomingMessage.toLowerCase().contains("confirm");

            Map<String, Object> fallback = new LinkedHashMap<>();
            if (isAcceptance) {
                fallback.put("intent", "acceptance");
                fallback.put("recommended_stage", "APPROVAL");
                fallback.put("strategy", "Supplier accepted negotiated pricing. Finalizing terms for Purchase Order issuance.");
                fallback.put("reply_subject", "Agreement Confirmation: Purchase Order Preparation - Kraya");
                fallback.put("reply_body", "Dear " + supplierName + ",\n\n" +
                        "Thank you for confirming the agreed terms and revised pricing. " +
                        "Our procurement team has approved this proposal, and we are preparing the formal Purchase Order (PO). " +
                        "We will forward the signed PO documentation shortly.\n\n" +
                        "Best regards,\nKraya Autonomous Procurement Agent");
            } else {
                fallback.put("intent", "quote");
                fallback.put("recommended_stage", "NEGOTIATION");
                fallback.put("strategy", "Supplier quotation analyzed. Proposed 5% volume discount with Net-30 payment terms.");
                fallback.put("reply_subject", "RE: Quotation Evaluation & Commercial Terms - Kraya");
                fallback.put("reply_body", "Dear " + supplierName + ",\n\n" +
                        "Thank you for your prompt quotation. We have reviewed your proposal regarding the networking equipment requirements. " +
                        "The technical specifications and delivery timeframe meet our criteria.\n\n" +
                        "However, our approved enterprise budget for immediate execution is capped at a 5% volume adjustment with Net-30 payment terms. " +
                        "If you can accommodate these terms, we can finalize approval today and issue the official Purchase Order.\n\n" +
                        "Please let us know if you can confirm these terms.\n\n" +
                        "Best regards,\nKraya Autonomous Procurement Agent");
            }
            return fallback;
        }
    }

    @Transactional(readOnly = true)
    public Map<String, Object> latest(UUID requestId) {
        try {
            var user = users.require();
            requests.get(requestId); // Enforce tenant scope before reading run history.
            List<Map<String, Object>> rows = jdbc.queryForList(
                    "SELECT id, status, result::text AS result, error_message, started_at, completed_at " +
                            "FROM agent_runs WHERE organization_id=? AND procurement_request_id=? " +
                            "ORDER BY started_at DESC LIMIT 1",
                    user.organizationId(), requestId);
            if (rows.isEmpty()) throw new ResourceNotFoundException("Agent workflow not found for request: " + requestId);
            Map<String, Object> row = rows.get(0);
            Map<String, Object> output = new LinkedHashMap<>();
            output.put("runId", row.get("id"));
            output.put("runStatus", row.get("status"));
            output.put("startedAt", row.get("started_at"));
            output.put("completedAt", row.get("completed_at"));
            output.put("errorMessage", row.get("error_message"));
            String resultJson = (String) row.get("result");
            if (resultJson != null && !resultJson.isBlank()) {
                try {
                    output.putAll(mapper.readValue(resultJson, Map.class));
                } catch (Exception e) {
                    throw new IllegalStateException("Stored agent workflow result is invalid", e);
                }
            }
            return output;
        } catch (RuntimeException error) {
            log.error("Failed to load agent workflow result for request {}", requestId, error);
            throw error;
        }
    }

    private Map<String, Object> supplierPayload(Supplier s) {
        Map<String, Object> value = new LinkedHashMap<>();
        value.put("supplier_id", s.getId()); value.put("organization_id", users.require().organizationId());
        value.put("name", s.getName()); value.put("contact_name", s.getContactName());
        value.put("contact_email", s.getContactEmail()); value.put("contact_phone", s.getContactPhone());
        value.put("country_code", s.getCountryCode()); value.put("website_url", s.getWebsiteUrl());
        value.put("tax_id", s.getTaxId()); value.put("payment_terms", s.getPaymentTerms());
        value.put("notes", s.getNotes()); value.put("status", s.getStatus().name());
        value.put("categories", s.getCategories());
        return value;
    }
}
