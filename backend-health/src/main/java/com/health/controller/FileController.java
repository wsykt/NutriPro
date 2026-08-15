package com.health.controller;

import com.health.dto.ApiResponse;
import com.health.service.FileService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
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
     * @param avatar 头像图片（MultipartFile）
     * @param userId 目标用户 ID
     * @return ApiResponse.data = 头像访问 URL
     */
    @PostMapping("/uploadAvatar")
    public ApiResponse<String> uploadAvatar(
            @RequestParam("avatar") MultipartFile avatar,
            @RequestParam("userId") Integer userId
    ) {
        if (userId == null || userId <= 0) {
            return ApiResponse.error(400, "用户ID不能为空");
        }
        try {
            return fileService.uploadAvatar(avatar, userId);
        } catch (Exception e) {
            log.error("头像上传异常: userId={}, error={}", userId, e.getMessage(), e);
            return ApiResponse.error(500, "服务器内部错误：头像上传失败");
        }
    }
}
