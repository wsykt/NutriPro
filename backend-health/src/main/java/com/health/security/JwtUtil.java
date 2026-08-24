package com.health.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import java.security.SecureRandom;
import java.util.Base64;
import java.util.Date;

/**
 * JWT 工具类：签发/解析/校验 token。
 * 对解析过程中可能出现的异常（sub 非数字、字段缺失等）均做了 null 安全处理。
 */
@Component
public class JwtUtil {

    private static final Logger log = LoggerFactory.getLogger(JwtUtil.class);

    /** 旧版本内置的固定默认密钥（已废弃）：检测到即轮换，防止使用已知密钥伪造 token。 */
    private static final String LEGACY_DEFAULT_SECRET = "RkVCRUNBMDUyNzlDQjAzQkI0OUJBNjM4MjIxRjY3QUI=";

    @Value("${health.jwt.secret:}")
    private String secret;

    @Value("${health.jwt.expiration}")
    private Long expiration;

    @PostConstruct
    public void init() {
        if (secret == null || secret.trim().isEmpty() || LEGACY_DEFAULT_SECRET.equals(secret.trim())) {
            byte[] keyBytes = new byte[32];
            new SecureRandom().nextBytes(keyBytes);
            secret = Base64.getEncoder().encodeToString(keyBytes);
            log.warn("未配置安全的 JWT_SECRET，已自动生成本次启动随机密钥（重启后所有已登录 token 将失效）；生产环境必须通过环境变量 JWT_SECRET 指定固定密钥");
        }
    }

    public String generateToken(Integer userId, String username, String role) {
        Date now = new Date();
        Date expiryDate = new Date(now.getTime() + expiration);

        return Jwts.builder()
                .setSubject(String.valueOf(userId))
                .claim("username", username)
                .claim("role", role)
                .setIssuedAt(now)
                .setExpiration(expiryDate)
                .signWith(SignatureAlgorithm.HS512, secret)
                .compact();
    }

    public Claims parseToken(String token) {
        return Jwts.parser()
                .setSigningKey(secret)
                .parseClaimsJws(token)
                .getBody();
    }

    public Integer getUserIdFromToken(String token) {
        String subject = parseToken(token).getSubject();
        if (subject == null) return null;
        try {
            return Integer.parseInt(subject.trim());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    public String getUsernameFromToken(String token) {
        return (String) parseToken(token).get("username");
    }

    public String getRoleFromToken(String token) {
        Object role = parseToken(token).get("role");
        return role == null ? "user" : role.toString();
    }

    public boolean validateToken(String token) {
        try {
            Claims claims = parseToken(token);
            return claims != null && claims.getSubject() != null;
        } catch (Exception e) {
            return false;
        }
    }
}
