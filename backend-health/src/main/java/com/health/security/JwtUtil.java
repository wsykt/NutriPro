package com.health.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.Date;

/**
 * JWT 工具类：签发/解析/校验 token。
 * 对解析过程中可能出现的异常（sub 非数字、字段缺失等）均做了 null 安全处理。
 */
@Component
public class JwtUtil {

    @Value("${health.jwt.secret}")
    private String secret;

    @Value("${health.jwt.expiration}")
    private Long expiration;

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
