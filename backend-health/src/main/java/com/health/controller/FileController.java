package com.health.controller;

import com.health.dto.ApiResponse;
import com.health.entity.User;
import com.health.service.FileService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

/**
 * 文件上传控制器
 * 提供用户头像上传接口 POST /api/file/uploadAvatar
 */
@RestController
@RequestMapping("/api/file")
public class FileController {

    private static final Logger log = LoggerFactory.getLogger(FileController.class);

    private final FileService fileService;

    public FileController(FileService fileService) {
        this.fileService = fileService;
    }

    /**
     * 用户头像上传接口
     *
     * <p>安全说明：头像归属以当前登录用户为准，忽略客户端传入的 userId，
     * 防止越权覆盖/删除他人头像（IDOR）。</p>
     *
     * @param avatar 头像图片（MultipartFile）
     * @param authentication 当前登录用户（Spring Security 注入）
     * @return ApiResponse.data = 头像访问 URL
     */
    @PostMapping("/uploadAvatar")
    public ApiResponse<String> uploadAvatar(
            @RequestParam("avatar") MultipartFile avatar,
            @RequestParam(value = "userId", required = false) Integer ignoredClientUserId,
            Authentication authentication
    ) {
        User user = extractUser(authentication);
        if (user == null) {
            return ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录");
        }
        try {
            return fileService.uploadAvatar(avatar, user.getUserId());
        } catch (Exception e) {
            log.error("头像上传异常: userId={}, error={}", user.getUserId(), e.getMessage(), e);
            return ApiResponse.error(500, "服务器内部错误：头像上传失败");
        }
    }

    private User extractUser(Authentication authentication) {
        if (authentication == null || authentication.getPrincipal() == null) return null;
        Object principal = authentication.getPrincipal();
        if (principal instanceof User) return (User) principal;
        return null;
    }
}
