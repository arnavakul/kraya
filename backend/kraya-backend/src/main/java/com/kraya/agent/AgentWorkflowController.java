package com.kraya.agent;

import org.springframework.web.bind.annotation.*;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/requests/{requestId}/agent-workflows")
public class AgentWorkflowController {
    private final AgentWorkflowService service;
    public AgentWorkflowController(AgentWorkflowService service) { this.service = service; }

    @PostMapping
    public Map<String, Object> run(@PathVariable UUID requestId) {
        return service.run(requestId);
    }

    @GetMapping("/latest")
    public Map<String, Object> latest(@PathVariable UUID requestId) {
        return service.latest(requestId);
    }

    @PostMapping("/approve-rfq")
    public Map<String, Object> approveAndDispatchRfq(
            @PathVariable UUID requestId,
            @RequestBody(required = false) Map<String, Object> dispatchPayload) {
        return service.approveAndDispatchRfq(requestId, dispatchPayload);
    }

    @PostMapping("/thread/message")
    public Map<String, Object> handleThreadMessage(
            @PathVariable UUID requestId,
            @RequestBody Map<String, Object> messagePayload) {
        return service.handleThreadMessage(requestId, messagePayload);
    }

    @PostMapping("/thread/approve-draft")
    public Map<String, Object> approveThreadDraft(
            @PathVariable UUID requestId,
            @RequestBody(required = false) Map<String, Object> payload) {
        return service.approveThreadDraft(requestId, payload);
    }

    @PostMapping("/thread/discard-draft")
    public Map<String, Object> discardThreadDraft(@PathVariable UUID requestId) {
        return service.discardThreadDraft(requestId);
    }

    @PostMapping("/sync-status")
    public Map<String, Object> syncWorkflowStatus(@PathVariable UUID requestId) {
        return service.syncWorkflowStatus(requestId);
    }
}
