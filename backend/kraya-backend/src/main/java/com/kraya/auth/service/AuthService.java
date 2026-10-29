package com.kraya.auth.service;

import com.kraya.auth.dto.AuthResult;
import com.kraya.auth.dto.LoginRequest;
import com.kraya.auth.dto.LoginResponse;
import com.kraya.common.exception.UnauthorizedException;
import com.kraya.security.JwtService;
import com.kraya.user.entity.User;
import com.kraya.user.entity.UserStatus;
import com.kraya.user.repository.UserRepository;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthService {

    private static final String INVALID_CREDENTIALS = "Invalid email or password";

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final RefreshTokenService refreshTokenService;

    // Compared against when the email is unknown, so response time doesn't reveal which emails exist.
    private final String dummyHash;

    public AuthService(
            UserRepository userRepository,
            PasswordEncoder passwordEncoder,
            JwtService jwtService,
            RefreshTokenService refreshTokenService
    ) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.refreshTokenService = refreshTokenService;
        this.dummyHash = passwordEncoder.encode("kraya-timing-dummy");
    }

    @Transactional
    public AuthResult login(LoginRequest request) {
        String email = request.email().trim().toLowerCase();

        User user = userRepository.findByEmail(email).orElse(null);
        String hash = user != null ? user.getPasswordHash() : dummyHash;
        boolean passwordOk = passwordEncoder.matches(request.password(), hash);

        if (user == null || !passwordOk) {
            throw new UnauthorizedException(INVALID_CREDENTIALS);
        }
        requireActive(user);

        return new AuthResult(toResponse(user), refreshTokenService.issue(user));
    }

    @Transactional(noRollbackFor = UnauthorizedException.class)
    public AuthResult refresh(String rawRefreshToken) {
        RefreshTokenService.Rotated rotated = refreshTokenService.rotate(rawRefreshToken);
        requireActive(rotated.user());
        return new AuthResult(toResponse(rotated.user()), rotated.rawToken());
    }

    public void logout(String rawRefreshToken) {
        refreshTokenService.revoke(rawRefreshToken);
    }

    private void requireActive(User user) {
        if (user.getStatus() != UserStatus.ACTIVE) {
            throw new UnauthorizedException("User account is not active");
        }
    }

    private LoginResponse toResponse(User user) {
        return new LoginResponse(
                user.getId(),
                user.getOrganization().getId(),
                user.getEmail(),
                user.getRole().name(),
                jwtService.generateToken(user.getEmail())
        );
    }
}