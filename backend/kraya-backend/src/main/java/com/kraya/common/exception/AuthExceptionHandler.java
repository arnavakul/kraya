package com.kraya.common.exception;

import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.OffsetDateTime;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Runs before GlobalExceptionHandler so 401/400 aren't swallowed by its catch-all 500.
 * Same JSON shape as the existing error responses.
 */
@RestControllerAdvice
@Order(Ordered.HIGHEST_PRECEDENCE)
public class AuthExceptionHandler {

    @ExceptionHandler(UnauthorizedException.class)
    public ResponseEntity<Map<String, Object>> unauthorized(UnauthorizedException ex) {
        return body(HttpStatus.UNAUTHORIZED, ex.getMessage());
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<Map<String, Object>> malformedBody(HttpMessageNotReadableException ex) {
        return body(HttpStatus.BAD_REQUEST, "Malformed request body");
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> invalid(MethodArgumentNotValidException ex) {
        String message = ex.getBindingResult().getFieldErrors().stream()
                .findFirst()
                .map(e -> e.getField() + " " + e.getDefaultMessage())
                .orElse("Validation failed");
        return body(HttpStatus.BAD_REQUEST, message);
    }

    private static ResponseEntity<Map<String, Object>> body(HttpStatus status, String message) {
        Map<String, Object> b = new LinkedHashMap<>();
        b.put("timestamp", OffsetDateTime.now().toString());
        b.put("status", status.value());
        b.put("error", status.name());
        b.put("message", message);
        return ResponseEntity.status(status).body(b);
    }
}