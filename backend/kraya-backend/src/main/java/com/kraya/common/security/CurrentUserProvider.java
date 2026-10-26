package com.kraya.common.security;

import com.kraya.common.exception.UnauthorizedException;
import com.kraya.user.entity.User;
import com.kraya.user.entity.UserStatus;
import com.kraya.user.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Component
public class CurrentUserProvider {

    private static final Logger log = LoggerFactory.getLogger(CurrentUserProvider.class);

    private final UserRepository userRepository;

    public CurrentUserProvider(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Transactional(readOnly = true)
    public CurrentUser require() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !auth.isAuthenticated() || auth instanceof AnonymousAuthenticationToken) {
            throw new UnauthorizedException("Not authenticated");
        }

        User user = resolve(auth).orElseThrow(() -> {
            Object principal = auth.getPrincipal();
            log.warn("Authenticated principal could not be mapped to a user (principal type: {})",
                    principal == null ? "null" : principal.getClass().getName());
            return new UnauthorizedException("Not authenticated");
        });

        if (user.getStatus() != UserStatus.ACTIVE) {
            throw new UnauthorizedException("User account is not active");
        }
        return new CurrentUser(user.getId(), user.getOrganization().getId(), user.getRole());
    }

    /** Works whatever the JWT filter stored as principal: the User entity, a UserDetails, or the email. */
    private Optional<User> resolve(Authentication auth) {
        Object principal = auth.getPrincipal();
        if (principal instanceof User entity) {
            return userRepository.findById(entity.getId());
        }
        if (principal instanceof UserDetails details) {
            return userRepository.findByEmail(details.getUsername().trim().toLowerCase());
        }
        return userRepository.findByEmail(auth.getName().trim().toLowerCase());
    }
}