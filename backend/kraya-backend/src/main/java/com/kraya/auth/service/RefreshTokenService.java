package com.kraya.auth.service;

import com.kraya.auth.entity.RefreshToken;
import com.kraya.auth.repository.RefreshTokenRepository;
import com.kraya.common.exception.UnauthorizedException;
import com.kraya.user.entity.User;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.time.Duration;
import java.time.Instant;
import java.util.Base64;
import java.util.HexFormat;

@Service
public class RefreshTokenService {

    private static final SecureRandom RANDOM = new SecureRandom();

    private final RefreshTokenRepository repository;
    private final Duration ttl;

    public RefreshTokenService(
            RefreshTokenRepository repository,
            @Value("${kraya.auth.refresh-token-days:7}") long days
    ) {
        this.repository = repository;
        this.ttl = Duration.ofDays(days);
    }

    public record Rotated(User user, String rawToken) {
    }

    @Transactional
    public String issue(User user) {
        String raw = newRawToken();
        repository.save(new RefreshToken(user, hash(raw), Instant.now().plus(ttl)));
        return raw;
    }

    /**
     * Single-use rotation. Presenting an already-revoked token means it was
     * replayed (likely stolen), so every session of that user is revoked.
     * noRollbackFor keeps that revocation when we throw.
     */
    @Transactional(noRollbackFor = UnauthorizedException.class)
    public Rotated rotate(String rawToken) {
        if (rawToken == null || rawToken.isBlank()) {
            throw invalid();
        }
        Instant now = Instant.now();

        RefreshToken current = repository.findByTokenHash(hash(rawToken))
                .orElseThrow(RefreshTokenService::invalid);

        if (current.isRevoked()) {
            repository.revokeAllForUser(current.getUser().getId(), now);
            throw invalid();
        }
        if (current.isExpired(now)) {
            throw invalid();
        }

        current.revoke(now);
        User user = current.getUser();
        return new Rotated(user, issue(user));
    }

    @Transactional
    public void revoke(String rawToken) {
        if (rawToken == null || rawToken.isBlank()) {
            return;
        }
        repository.findByTokenHash(hash(rawToken))
                .ifPresent(t -> t.revoke(Instant.now()));
    }

    private static UnauthorizedException invalid() {
        return new UnauthorizedException("Session expired. Please log in again.");
    }

    private static String newRawToken() {
        byte[] bytes = new byte[32];
        RANDOM.nextBytes(bytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }

    private static String hash(String raw) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256")
                    .digest(raw.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(digest);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }
}