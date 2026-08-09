package com.health.service;

import com.health.dto.LoginRequest;
import com.health.dto.RegisterRequest;
import com.health.dto.ResetPasswordRequest;
import com.health.entity.User;
import com.health.repository.UserRepository;
import com.health.security.JwtUtil;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import lombok.extern.slf4j.Slf4j;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@Service
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;

    public AuthService(UserRepository userRepository, PasswordEncoder passwordEncoder, JwtUtil jwtUtil) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtUtil = jwtUtil;
    }

    public Map<String, Object> register(RegisterRequest req) {
        log.info("开始用户注册, username={}", req.getUsername());
        if (req.getUsername() == null || req.getUsername().trim().isEmpty()) {
            throw new RuntimeException("用户名不能为空");
        }
        if (req.getPassword() == null || req.getPassword().length() < 6) {
            throw new RuntimeException("密码长度至少 6 位");
        }
        if (userRepository.existsByUsername(req.getUsername())) {
            throw new RuntimeException("用户名已被占用");
        }

        User user = new User(req.getUsername(), passwordEncoder.encode(req.getPassword()));
        if (req.getGender() != null) user.setGender(req.getGender());
        if (req.getHeight() != null) user.setHeight(req.getHeight());
        if (req.getWeight() != null) user.setWeight(req.getWeight());
        if (req.getAge() != null) user.setAge(req.getAge());
        if (req.getCrowdType() != null) user.setCrowdType(req.getCrowdType());

        userRepository.save(user);

        String token = jwtUtil.generateToken(user.getUserId(), user.getUsername(), user.getRole());
        Map<String, Object> result = new HashMap<>();
        result.put("access_token", token);
        result.put("token_type", "bearer");
        result.put("user_id", user.getUserId());
        result.put("username", user.getUsername());
        result.put("crowd_type", user.getCrowdType());
        result.put("role", user.getRole());
        return result;
    }

    public Map<String, Object> login(LoginRequest req) {
        if (req.getUsername() == null || req.getUsername().trim().isEmpty()) {
            throw new RuntimeException("用户名不能为空");
        }
        User user = userRepository.findByUsername(req.getUsername())
                .orElseThrow(() -> new RuntimeException("用户名或密码错误"));
        if (!passwordEncoder.matches(req.getPassword(), user.getPassword())) {
            throw new RuntimeException("用户名或密码错误");
        }

        String token = jwtUtil.generateToken(user.getUserId(), user.getUsername(), user.getRole());
        Map<String, Object> result = new HashMap<>();
        result.put("access_token", token);
        result.put("token_type", "bearer");
        result.put("user_id", user.getUserId());
        result.put("username", user.getUsername());
        result.put("crowd_type", user.getCrowdType());
        result.put("role", user.getRole());
        log.info("用户登录成功, userId={}", user.getUserId());
        return result;
    }

    public Map<String, Object> resetPassword(ResetPasswordRequest req) {
        if (req.getUsername() == null || req.getUsername().trim().isEmpty()) {
            throw new RuntimeException("用户名不能为空");
        }
        if (req.getNewPassword() == null || req.getNewPassword().length() < 6) {
            throw new RuntimeException("新密码长度至少 6 位");
        }

        User user = userRepository.findByUsername(req.getUsername())
                .orElseThrow(() -> new RuntimeException("该用户不存在"));

        // 安全加固：必须携带旧密码且校验通过（BCrypt matches），防止仅凭用户名即可接管账号
        if (req.getOldPassword() == null || req.getOldPassword().isEmpty()
                || !passwordEncoder.matches(req.getOldPassword(), user.getPassword())) {
            throw new RuntimeException("旧密码不正确");
        }

        user.setPassword(passwordEncoder.encode(req.getNewPassword()));
        userRepository.save(user);

        Map<String, Object> result = new HashMap<>();
        result.put("user_id", user.getUserId());
        result.put("username", user.getUsername());
        result.put("message", "密码重置成功");
        return result;
    }
}
