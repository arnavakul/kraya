package com.kraya.user.controller;

import com.kraya.user.dto.CreateUserRequest;
import com.kraya.user.dto.UpdateUserRequest;
import com.kraya.user.dto.UserResponse;
import com.kraya.user.service.UserService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @PostMapping
    public ResponseEntity<UserResponse> create(
            @Valid @RequestBody CreateUserRequest request
    ) {
        UserResponse response = userService.create(request);

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(response);
    }

    @GetMapping("/{id}")
    public ResponseEntity<UserResponse> getById(
            @PathVariable UUID id
    ) {
        return ResponseEntity.ok(userService.getById(id));
    }

    @GetMapping
    public ResponseEntity<List<UserResponse>> getByOrganizationId(
            @RequestParam UUID organizationId
    ) {
        return ResponseEntity.ok(userService.getByOrganizationId(organizationId));
    }

    @PatchMapping("/{id}")
    public ResponseEntity<UserResponse> update(
            @PathVariable UUID id,
            @Valid @RequestBody UpdateUserRequest request
    ) {
        return ResponseEntity.ok(
                userService.update(id, request)
        );
    }

    @PatchMapping("/{id}/suspend")
    public ResponseEntity<UserResponse> suspend(
            @PathVariable UUID id
    ) {
        return ResponseEntity.ok(
                userService.suspend(id)
        );
    }
}