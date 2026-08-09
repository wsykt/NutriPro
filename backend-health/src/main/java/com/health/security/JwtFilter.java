package com.health.security;

import com.health.entity.User;
import com.health.repository.UserRepository;
import org.slf4j.MDC;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Collections;

/**
 * JWT 鉴权过滤器：解析 Authorization header 中的 Bearer token，
 * 若 token 合法且对应的用户存在，则将用户信息写入 Spring Security 上下文。
 *
 * 任何异常都被安全地捕获，避免 token 格式/内容异常导致请求直接返回 500。
 */
@Component
public class JwtFilter extends OncePerRequestFilter {

    private final JwtUtil jwtUtil;
    private final UserRepository userRepository;

    public JwtFilter(JwtUtil jwtUtil, UserRepository userRepository) {
        this.jwtUtil = jwtUtil;
        this.userRepository = userRepository;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        // 预检请求直接放行，交给 CorsFilter/CorsConfigurationSource 处理
        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            filterChain.doFilter(request, response);
            return;
        }

        String authHeader = request.getHeader("Authorization");

        try {
            if (authHeader != null && authHeader.startsWith("Bearer ")) {
                String token = authHeader.substring(7);

                try {
                    if (jwtUtil.validateToken(token)) {
                        Integer userId = jwtUtil.getUserIdFromToken(token);
                        String role = jwtUtil.getRoleFromToken(token);

                        if (userId != null) {
                            User user = userRepository.findById(userId).orElse(null);
                            if (user != null) {
                                MDC.put("userId", String.valueOf(userId));
                                String grantedRole = (role != null && !role.isEmpty()) ? role : "user";
                                UsernamePasswordAuthenticationToken authentication =
                                        new UsernamePasswordAuthenticationToken(
                                                user,
                                                null,
                                                Collections.singletonList(new SimpleGrantedAuthority("ROLE_" + grantedRole.toUpperCase()))
                                        );
                                SecurityContextHolder.getContext().setAuthentication(authentication);
                            }
                        }
                    }
                } catch (Exception ignored) {
                    SecurityContextHolder.clearContext();
                }
            }

            filterChain.doFilter(request, response);
        } finally {
            MDC.remove("userId");
        }
    }
}
