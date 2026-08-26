package com.kraya.common.exception;

import com.kraya.common.api.ApiError;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiError> handleException(
            Exception exception,
            HttpServletRequest request
    ) {
        String correlationId = UUID.randomUUID().toString();

        ApiError error = new ApiError(
                "INTERNAL_ERROR",
                "An unexpected error occurred.",
                List.of(),
                Instant.now(),
                correlationId
        );

        return ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(error);
    }
}