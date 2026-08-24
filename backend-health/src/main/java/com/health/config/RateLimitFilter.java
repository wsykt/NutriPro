package com.health.config;

import com.health.security.JwtUtil;
import com.health.util.RateLimiter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;

/**
 * 请求限流过滤器（P2 安全加固）。
 *
 * 策略（纯内存，单实例适用）：
 * 1. /api/auth/**（登录/注册/重置密码）→ 按客户端 IP 限流，默认 10 次 / 5 分钟，防爆破。
 * 2. /api/ai/**（LLM 咨询等烧 token 的接口）→ 按用户 ID 限流（无 token 时回退 IP），默认 30 次 / 分钟。
 *
 * 超限返回 HTTP 429。阈值可通过 application.yml 的 health.rate-limit.* 调整。
 */
@Component
public class RateLimitFilter extends OncePerRequestFilter {

    private static final Logger log = LoggerFactory.getLogger(RateLimitFilter.class);

    private final JwtUtil jwtUtil;

    @Value("${health.rate-limit.auth-max:10}")
    private int authMax;

    @Value("${health.rate-limit.auth-window-seconds:300}")
    private long authWindowSeconds;

    @Value("${health.rate-limit.ai-max:30}")
    private int aiMax;

    @Value("${health.rate-limit.ai-window-seconds:60}")
    private long aiWindowSeconds;

    private volatile RateLimiter authLimiter;
    private volatile RateLimiter aiLimiter;

    public RateLimitFilter(JwtUtil jwtUtil) {
        this.jwtUtil = jwtUtil;
    }

    private RateLimiter getAuthLimiter() {
        RateLimiter limiter = authLimiter;
        if (limiter == null) {
            synchronized (this) {
                if (authLimiter == null) {
                    authLimiter = new RateLimiter(authMax, authWindowSeconds * 1000L);
                }
                limiter = authLimiter;
            }
        }
        return limiter;
    }

    private RateLimiter getAiLimiter() {
        RateLimiter limiter = aiLimiter;
        if (limiter == null) {
            synchronized (this) {
                if (aiLimiter == null) {
                    aiLimiter = new RateLimiter(aiMax, aiWindowSeconds * 1000L);
                }
                limiter = aiLimiter;
            }
        }
        return limiter;
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String uri = request.getRequestURI();
        // 覆盖：登录类、AI 生成/咨询类、文章 AI 生成类（烧 token 的接口）
        return !(uri.startsWith("/api/auth/")
                || uri.startsWith("/api/ai/")
                || isArticleGenerationPath(uri));
    }

    /** 文章 AI 生成/知识库写入类路径（烧 token，需限流） */
    private boolean isArticleGenerationPath(String uri) {
        if (!uri.startsWith("/api/articles/")) return false;
        return uri.contains("/generate")
                || uri.contains("/import-mother")
                || uri.contains("/regenerate")
                || uri.contains("/knowledge/ingest");
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        String uri = request.getRequestURI();
        boolean allowed;
        String key;

        if (uri.startsWith("/api/auth/")) {
            // 登录类接口：按 IP 限流（无需解析 token）
            key = clientIp(request);
            allowed = getAuthLimiter().tryAcquire(key);
        } else {
            // AI 类接口：优先按用户 ID（从 Bearer token 解析），未认证时回退 IP
            key = resolveUserId(request);
            allowed = getAiLimiter().tryAcquire(key);
        }

        if (!allowed) {
            log.warn("限流拦截: uri={}, key={}", uri, key);
            response.setStatus(429);
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write("{\"code\":429,\"message\":\"请求过于频繁，请稍后再试\"}");
            return;
        }
        filterChain.doFilter(request, response);
    }

    private String resolveUserId(HttpServletRequest request) {
        String auth = request.getHeader("Authorization");
        if (auth != null && auth.startsWith("Bearer ")) {
            try {
                Integer userId = jwtUtil.getUserIdFromToken(auth.substring(7));
                if (userId != null) {
                    return "user:" + userId;
                }
            } catch (Exception ignored) {
                // token 无效或过期：回退 IP 维度
            }
        }
        return "ip:" + clientIp(request);
    }

    private String clientIp(HttpServletRequest request) {
        // 不使用 X-Forwarded-For（客户端可伪造绕过 IP 维度限流）。
        // 若部署在反向代理后，应在此按可信代理链解析真实 IP（或改用网关层限流）。
        String remoteAddr = request.getRemoteAddr();
        return remoteAddr != null ? remoteAddr : "unknown";
    }
}
