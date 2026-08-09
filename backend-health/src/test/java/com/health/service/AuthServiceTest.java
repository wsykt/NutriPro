package com.health.service;

import com.health.dto.LoginRequest;
import com.health.dto.RegisterRequest;
import com.health.dto.ResetPasswordRequest;
import com.health.entity.User;
import com.health.repository.UserRepository;
import com.health.security.JwtUtil;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * AuthService 单元测试
 * 覆盖注册、登录、重置密码的正常与异常路径
 */
@DisplayName("认证服务测试")
class AuthServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @Mock
    private JwtUtil jwtUtil;

    @InjectMocks
    private AuthService authService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    // ========== 注册测试 ==========

    @Test
    @DisplayName("注册成功 - 正常返回 token 和用户信息")
    void register_Success() {
        RegisterRequest req = new RegisterRequest();
        req.setUsername("testuser");
        req.setPassword("123456");
        req.setGender("男");
        req.setAge(25);
        req.setHeight(175.0);
        req.setWeight(70.0);
        req.setCrowdType("健身");

        when(userRepository.existsByUsername("testuser")).thenReturn(false);
        when(passwordEncoder.encode("123456")).thenReturn("$2a$encoded");
        when(userRepository.save(any(User.class))).thenAnswer(invocation -> {
            User u = invocation.getArgument(0);
            u.setUserId(1);
            return u;
        });
        when(jwtUtil.generateToken(1, "testuser", "user")).thenReturn("mock-jwt-token");

        Map<String, Object> result = authService.register(req);

        assertNotNull(result);
        assertEquals("mock-jwt-token", result.get("access_token"));
        assertEquals("bearer", result.get("token_type"));
        assertEquals("testuser", result.get("username"));
        assertEquals(1, result.get("user_id"));
        verify(userRepository).save(any(User.class));
    }

    @Test
    @DisplayName("注册失败 - 用户名为空")
    void register_EmptyUsername() {
        RegisterRequest req = new RegisterRequest();
        req.setUsername("");
        req.setPassword("123456");

        RuntimeException ex = assertThrows(RuntimeException.class, () -> authService.register(req));
        assertEquals("用户名不能为空", ex.getMessage());
    }

    @Test
    @DisplayName("注册失败 - 用户名为null")
    void register_NullUsername() {
        RegisterRequest req = new RegisterRequest();
        req.setUsername(null);
        req.setPassword("123456");

        RuntimeException ex = assertThrows(RuntimeException.class, () -> authService.register(req));
        assertEquals("用户名不能为空", ex.getMessage());
    }

    @Test
    @DisplayName("注册失败 - 密码过短")
    void register_ShortPassword() {
        RegisterRequest req = new RegisterRequest();
        req.setUsername("testuser");
        req.setPassword("123");

        RuntimeException ex = assertThrows(RuntimeException.class, () -> authService.register(req));
        assertEquals("密码长度至少 6 位", ex.getMessage());
    }

    @Test
    @DisplayName("注册失败 - 密码为null")
    void register_NullPassword() {
        RegisterRequest req = new RegisterRequest();
        req.setUsername("testuser");
        req.setPassword(null);

        RuntimeException ex = assertThrows(RuntimeException.class, () -> authService.register(req));
        assertEquals("密码长度至少 6 位", ex.getMessage());
    }

    @Test
    @DisplayName("注册失败 - 用户名已存在")
    void register_DuplicateUsername() {
        RegisterRequest req = new RegisterRequest();
        req.setUsername("existing");
        req.setPassword("123456");

        when(userRepository.existsByUsername("existing")).thenReturn(true);

        RuntimeException ex = assertThrows(RuntimeException.class, () -> authService.register(req));
        assertEquals("用户名已被占用", ex.getMessage());
    }

    // ========== 登录测试 ==========

    @Test
    @DisplayName("登录成功 - 正常返回 token")
    void login_Success() {
        LoginRequest req = new LoginRequest("testuser", "123456");
        User user = new User("testuser", "$2a$encoded");
        user.setUserId(1);
        user.setRole("user");
        user.setCrowdType("普通人");

        when(userRepository.findByUsername("testuser")).thenReturn(Optional.of(user));
        when(passwordEncoder.matches("123456", "$2a$encoded")).thenReturn(true);
        when(jwtUtil.generateToken(1, "testuser", "user")).thenReturn("mock-jwt-token");

        Map<String, Object> result = authService.login(req);

        assertNotNull(result);
        assertEquals("mock-jwt-token", result.get("access_token"));
        assertEquals("testuser", result.get("username"));
    }

    @Test
    @DisplayName("登录失败 - 用户名为空")
    void login_EmptyUsername() {
        LoginRequest req = new LoginRequest("", "123456");

        RuntimeException ex = assertThrows(RuntimeException.class, () -> authService.login(req));
        assertEquals("用户名不能为空", ex.getMessage());
    }

    @Test
    @DisplayName("登录失败 - 用户不存在")
    void login_UserNotFound() {
        LoginRequest req = new LoginRequest("nouser", "123456");
        when(userRepository.findByUsername("nouser")).thenReturn(Optional.empty());

        RuntimeException ex = assertThrows(RuntimeException.class, () -> authService.login(req));
        assertEquals("用户名或密码错误", ex.getMessage());
    }

    @Test
    @DisplayName("登录失败 - 密码错误")
    void login_WrongPassword() {
        LoginRequest req = new LoginRequest("testuser", "wrongpwd");
        User user = new User("testuser", "$2a$encoded");
        user.setUserId(1);

        when(userRepository.findByUsername("testuser")).thenReturn(Optional.of(user));
        when(passwordEncoder.matches("wrongpwd", "$2a$encoded")).thenReturn(false);

        RuntimeException ex = assertThrows(RuntimeException.class, () -> authService.login(req));
        assertEquals("用户名或密码错误", ex.getMessage());
    }

    // ========== 重置密码测试 ==========

    @Test
    @DisplayName("重置密码成功")
    void resetPassword_Success() {
        ResetPasswordRequest req = new ResetPasswordRequest();
        req.setUsername("testuser");
        req.setNewPassword("newpass123");

        User user = new User("testuser", "$2a$old");
        user.setUserId(1);

        when(userRepository.findByUsername("testuser")).thenReturn(Optional.of(user));
        when(passwordEncoder.encode("newpass123")).thenReturn("$2a$newencoded");

        Map<String, Object> result = authService.resetPassword(req);

        assertNotNull(result);
        assertEquals("密码重置成功", result.get("message"));
        assertEquals("testuser", result.get("username"));
        verify(userRepository).save(user);
    }

    @Test
    @DisplayName("重置密码失败 - 用户不存在")
    void resetPassword_UserNotFound() {
        ResetPasswordRequest req = new ResetPasswordRequest();
        req.setUsername("nouser");
        req.setNewPassword("newpass123");

        when(userRepository.findByUsername("nouser")).thenReturn(Optional.empty());

        RuntimeException ex = assertThrows(RuntimeException.class, () -> authService.resetPassword(req));
        assertEquals("该用户不存在", ex.getMessage());
    }

    @Test
    @DisplayName("重置密码失败 - 新密码过短")
    void resetPassword_ShortNewPassword() {
        ResetPasswordRequest req = new ResetPasswordRequest();
        req.setUsername("testuser");
        req.setNewPassword("123");

        RuntimeException ex = assertThrows(RuntimeException.class, () -> authService.resetPassword(req));
        assertEquals("新密码长度至少 6 位", ex.getMessage());
    }
}
