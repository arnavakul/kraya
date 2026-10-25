package com.kraya.auth.dto;

/** Service-layer result: body for the client + raw refresh token for the cookie. */
public record AuthResult(LoginResponse response, String refreshToken) {
}