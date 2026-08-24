package com.health.controller;

import com.health.dto.LoginRequest;
import com.health.dto.RegisterRequest;
import com.health.dto.ResetPasswordRequest;
import com.health.service.AuthService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.health.dto.ApiResponse;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

/**
 * AuthController 单元测试
 * 使用纯 Mockito 验证 Controller 逻辑
 */
@DisplayName("认证控制器测试")
class AuthControllerTest {

    @Mock
    private AuthService authService;

    @InjectMocks
    private AuthController authController;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    @DisplayName("POST /api/auth/register - 注册成功返回 200")
    void register_Success() {
        Map<String, Object> mockResult = new HashMap<>();
        mockResult.put("access_token", "jwt-token");
        mockResult.put("user_id", 1);
        mockResult.put("username", "testuser");

        when(authService.register(any(RegisterRequest.class))).thenReturn(mockResult);

        RegisterRequest req = new RegisterRequest();
        req.setUsername("testuser");
        req.setPassword("123456");

        ResponseEntity<ApiResponse<Map<String, Object>>> response = authController.register(req);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals(200, response.getBody().getCode());
        assertEquals("testuser", response.getBody().getData().get("username"));
    }

    @Test
    @DisplayName("POST /api/auth/register - 注册失败返回 400")
    void register_Failure() {
        when(authService.register(any(RegisterRequest.class)))
                .thenThrow(new RuntimeException("用户名已被占用"));

        RegisterRequest req = new RegisterRequest();
        req.setUsername("existing");
        req.setPassword("123456");

        ResponseEntity<ApiResponse<Map<String, Object>>> response = authController.register(req);

        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        assertEquals("用户名已被占用", response.getBody().getMessage());
    }

    @Test
    @DisplayName("POST /api/auth/login - 登录成功返回 token")
    void login_Success() {
        Map<String, Object> mockResult = new HashMap<>();
        mockResult.put("access_token", "jwt-token-123");
        mockResult.put("user_id", 1);
        mockResult.put("username", "testuser");
        mockResult.put("role", "user");

        when(authService.login(any(LoginRequest.class))).thenReturn(mockResult);

        LoginRequest req = new LoginRequest("testuser", "123456");

        ResponseEntity<ApiResponse<Map<String, Object>>> response = authController.login(req);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals("jwt-token-123", response.getBody().getData().get("access_token"));
    }

    @Test
    @DisplayName("POST /api/auth/login - 密码错误返回 400")
    void login_WrongPassword() {
        when(authService.login(any(LoginRequest.class)))
                .thenThrow(new RuntimeException("用户名或密码错误"));

        LoginRequest req = new LoginRequest("testuser", "wrongpwd");

        ResponseEntity<ApiResponse<Map<String, Object>>> response = authController.login(req);

        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        assertEquals("用户名或密码错误", response.getBody().getMessage());
    }

    @Test
    @DisplayName("POST /api/auth/reset-password - 重置密码成功")
    void resetPassword_Success() {
        Map<String, Object> mockResult = new HashMap<>();
        mockResult.put("user_id", 1);
        mockResult.put("username", "testuser");
        mockResult.put("message", "密码重置成功");

        when(authService.resetPassword(any(ResetPasswordRequest.class))).thenReturn(mockResult);

        ResetPasswordRequest req = new ResetPasswordRequest();
        req.setUsername("testuser");
        req.setNewPassword("newpass123");

        ResponseEntity<ApiResponse<Map<String, Object>>> response = authController.resetPassword(req);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals("密码重置成功", response.getBody().getData().get("message"));
    }

    @Test
    @DisplayName("POST /api/auth/reset-password - 用户不存在返回 400")
    void resetPassword_UserNotFound() {
        when(authService.resetPassword(any(ResetPasswordRequest.class)))
                .thenThrow(new RuntimeException("该用户不存在"));

        ResetPasswordRequest req = new ResetPasswordRequest();
        req.setUsername("nouser");
        req.setNewPassword("newpass123");

        ResponseEntity<ApiResponse<Map<String, Object>>> response = authController.resetPassword(req);

        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
    }
}
