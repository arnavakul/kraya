package com.kraya.agent;

import tools.jackson.databind.ObjectMapper;
import com.kraya.common.security.CurrentUserProvider;
import com.kraya.supplier.entity.Supplier;
import com.kraya.supplier.entity.SupplierStatus;
import com.kraya.supplier.repository.SupplierRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.*;

@Service
public class AgentChatService {

    private static final Logger log = LoggerFactory.getLogger(AgentChatService.class);

    public static final List<String> PROGRESS_STAGES = List.of(
            "Requirement Analysis",
            "Supplier Discovery",
            "Quote Collection",
            "Evaluation & Comparison",
            "Recommendation"
    );

    private final CurrentUserProvider users;
    private final SupplierRepository suppliers;
    private final ObjectMapper mapper;
    private final RestClient agents;

    public AgentChatService(
            CurrentUserProvider users,
            SupplierRepository suppliers,
            ObjectMapper mapper,
            @Value("${kraya.agents.url:http://localhost:8000}") String agentUrl) {
        this.users = users;
        this.suppliers = suppliers;
        this.mapper = mapper;
        this.agents = RestClient.builder().baseUrl(agentUrl).build();
    }

    public Map<String, Object> chat(AgentChatController.ChatRequest request) {
        var user = users.require();

        String conversationId = (request.conversationId() != null && !request.conversationId().isBlank())
                ? request.conversationId()
                : UUID.randomUUID().toString();

        String query = request.message().trim();

        // Load real active suppliers from tenant database
        List<Map<String, Object>> supplierData = suppliers.findAllByOrganizationIdAndStatus(
                user.organizationId(), SupplierStatus.ACTIVE).stream().map(this::supplierPayload).toList();

        // 1. Dispatch dynamically to Python Agent Service (/chat)
        try {
            Map<String, Object> payload = new LinkedHashMap<>();
            payload.put("message", query);
            payload.put("suppliers", supplierData);

            @SuppressWarnings("unchecked")
            Map<String, Object> pythonResult = agents.post()
                    .uri("/chat")
                    .body(payload)
                    .retrieve()
                    .body(Map.class);

            if (pythonResult != null && pythonResult.containsKey("reply")) {
                Map<String, Object> response = new LinkedHashMap<>(pythonResult);
                response.put("conversationId", conversationId);
                return response;
            }

        } catch (Exception e) {
            log.warn("Dynamic agent call to Python /chat failed: {}", e.getMessage());
        }

        // 2. Graceful intelligent fallback if agent service is unreachable
        return buildFallbackResponse(conversationId, query, supplierData.size());
    }

    private Map<String, Object> buildFallbackResponse(String conversationId, String query, int supplierCount) {
        String reply = "I've received your inquiry: \"" + query + "\". " +
                "Your organization currently has " + supplierCount + " active suppliers in the catalog. " +
                "How can I assist you further with specifications, quotes, or risk analysis?";

        List<Map<String, Object>> steps = new ArrayList<>();
        steps.add(step("Extract and validate your requirements", "current"));
        steps.add(step("Discover and shortlist suitable suppliers", "pending"));
        steps.add(step("Collect quotes and compare options", "pending"));
        steps.add(step("Evaluate suppliers (price, delivery, reliability, risk)", "pending"));
        steps.add(step("Share my recommendation for your approval", "pending"));

        Map<String, Object> progress = new LinkedHashMap<>();
        progress.put("currentStage", "Requirement Analysis");
        progress.put("currentStageIndex", 0);
        progress.put("stages", PROGRESS_STAGES);

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("conversationId", conversationId);
        response.put("reply", reply);
        response.put("steps", steps);
        response.put("procurementProgress", progress);
        return response;
    }

    private Map<String, Object> step(String label, String status) {
        Map<String, Object> step = new LinkedHashMap<>();
        step.put("label", label);
        step.put("status", status); // "done", "current", "pending"
        step.put("done", "done".equals(status));
        return step;
    }

    private Map<String, Object> supplierPayload(Supplier s) {
        Map<String, Object> value = new LinkedHashMap<>();
        value.put("supplier_id", s.getId());
        value.put("organization_id", users.require().organizationId());
        value.put("name", s.getName());
        value.put("contact_name", s.getContactName());
        value.put("contact_email", s.getContactEmail());
        value.put("contact_phone", s.getContactPhone());
        value.put("country_code", s.getCountryCode());
        value.put("website_url", s.getWebsiteUrl());
        value.put("tax_id", s.getTaxId());
        value.put("payment_terms", s.getPaymentTerms());
        value.put("notes", s.getNotes());
        value.put("status", s.getStatus().name());
        value.put("categories", s.getCategories());
        return value;
    }
}
