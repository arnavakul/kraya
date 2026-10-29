package com.kraya.auth.controller;

import com.kraya.auth.dto.AuthResult;
import com.kraya.auth.dto.LoginRequest;
import com.kraya.auth.dto.LoginResponse;
import com.kraya.auth.dto.RegisterRequest;
import com.kraya.auth.service.AuthService;
import com.kraya.auth.service.RegistrationService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseCookie;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Duration;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private static final String REFRESH_COOKIE = "kraya_refresh";
    private static final String COOKIE_PATH = "/api/v1/auth";

    private final AuthService authService;
    private final RegistrationService registrationService;
    private final Duration refreshTtl;
    private final boolean cookieSecure;

    public AuthController(
            AuthService authService,
            RegistrationService registrationService,
            @Value("${kraya.auth.refresh-token-days:7}") long refreshDays,
            @Value("${kraya.auth.cookie-secure:false}") boolean cookieSecure
    ) {
        this.authService = authService;
        this.registrationService = registrationService;
        this.refreshTtl = Duration.ofDays(refreshDays);
        this.cookieSecure = cookieSecure;
    }

    @PostMapping("/register")
    public ResponseEntity<LoginResponse> register(@Valid @RequestBody RegisterRequest request) {
        registrationService.register(request);
        // Registration commits first, then we log the new user in with the same credentials.
        return withRefreshCookie(authService.login(new LoginRequest(request.email(), request.password())));
    }

    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        return withRefreshCookie(authService.login(request));
    }

    @PostMapping("/refresh")
    public ResponseEntity<LoginResponse> refresh(
            @CookieValue(name = REFRESH_COOKIE, required = false) String refreshToken
    ) {
        return withRefreshCookie(authService.refresh(refreshToken));
    }

    @PostMapping("/logout")
    public ResponseEntity<Void> logout(
            @CookieValue(name = REFRESH_COOKIE, required = false) String refreshToken
    ) {
        authService.logout(refreshToken);
        return ResponseEntity.noContent()
                .header(HttpHeaders.SET_COOKIE, cookie("", Duration.ZERO).toString())
                .build();
    }

    private ResponseEntity<LoginResponse> withRefreshCookie(AuthResult result) {
        return ResponseEntity.ok()
                .header(HttpHeaders.SET_COOKIE, cookie(result.refreshToken(), refreshTtl).toString())
                .header(HttpHeaders.CACHE_CONTROL, "no-store")
                .body(result.response());
    }

    private ResponseCookie cookie(String value, Duration maxAge) {
        return ResponseCookie.from(REFRESH_COOKIE, value)
                .httpOnly(true)
                .secure(cookieSecure)
                .sameSite("Strict")
                .path(COOKIE_PATH)
                .maxAge(maxAge)
                .build();
    }
}