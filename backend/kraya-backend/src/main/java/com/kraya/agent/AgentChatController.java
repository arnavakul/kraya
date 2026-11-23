package com.kraya.agent;

import org.springframework.web.bind.annotation.*;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/agent/chat")
public class AgentChatController {
    private final AgentChatService service;
    public AgentChatController(AgentChatService service) { this.service = service; }

    @PostMapping
    public Map<String, Object> chat(@Valid @RequestBody ChatRequest request) {
        return service.chat(request);
    }

    public record ChatRequest(
        @NotBlank @Size(max = 4000) String message,
        String conversationId
    ) {}
}
