package com.health.service;

import com.health.dto.ApiResponse;
import com.health.entity.User;
import com.health.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

/**
 * 文件上传服务
 * 负责头像上传、本地磁盘存储、旧头像自动清理逻辑
 * 仅使用本地磁盘，禁止任何云对象存储（OSS/MinIO）
 */
@Service
public class FileService {

    private static final Logger log = LoggerFactory.getLogger(FileService.class);

    /** 允许的图片格式 */
    private static final Set<String> ALLOWED_EXT = new HashSet<>(Arrays.asList("jpg", "jpeg", "png", "webp"));

    private final UserRepository userRepository;

    /** 本地磁盘存储路径（来自 application.yml upload.path） */
    @Value("${upload.path}")
    private String uploadPath;

    /** URL 访问前缀（来自 application.yml upload.access-prefix） */
    @Value("${upload.access-prefix}")
    private String accessPrefix;

    /** 单文件最大 MB（来自 application.yml upload.max-size-mb） */
    @Value("${upload.max-size-mb}")
    private int maxSizeMb;

    public FileService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    /**
     * 上传用户头像
     *
     * @param file   上传的图片文件
     * @param userId 用户 ID
     * @return ApiResponse.data = 头像访问 URL
     */
    @Transactional
    public ApiResponse<String> uploadAvatar(MultipartFile file, Integer userId) {
        // -----------------------------
        // ① 文件非空校验
        // -----------------------------
        if (file == null || file.isEmpty()) {
            return ApiResponse.error(400, "上传的图片不能为空");
        }

        // -----------------------------
        // ② 文件大小校验（限制 5MB）
        // -----------------------------
        long size = file.getSize();
        if (size > (long) maxSizeMb * 1024 * 1024) {
            return ApiResponse.error(400, "图片大小不能超过 " + maxSizeMb + "MB");
        }

        // -----------------------------
        // ③ 文件格式校验（jpg/png/webp/jpeg）
        // -----------------------------
        String originalFilename = file.getOriginalFilename();
        if (originalFilename == null || !originalFilename.contains(".")) {
            return ApiResponse.error(400, "图片文件名不合法");
        }
        String ext = originalFilename.substring(originalFilename.lastIndexOf('.') + 1).toLowerCase();
        if (!ALLOWED_EXT.contains(ext)) {
            return ApiResponse.error(400, "仅支持 jpg/jpeg/png/webp 格式的图片");
        }

        // -----------------------------
        // ④ 校验用户是否存在
        // -----------------------------
        Optional<User> opt = userRepository.findById(userId);
        if (!opt.isPresent()) {
            return ApiResponse.error(404, "用户不存在");
        }
        User user = opt.get();

        // -----------------------------
        // ⑤ 解析旧头像路径，尝试删除本地旧图片（非默认头像才删）
        //    删除失败仅打印日志，不阻断上传流程
        // -----------------------------
        String oldAvatar = user.getAvatar();
        if (oldAvatar != null && !oldAvatar.trim().isEmpty()) {
            try {
                // 旧头像格式：accessPrefix/xxx.ext → 需要拼出磁盘绝对路径
                if (oldAvatar.startsWith(accessPrefix)) {
                    String fileName = oldAvatar.substring(accessPrefix.length());
                    // 去除前缀的斜杠
                    if (fileName.startsWith("/")) fileName = fileName.substring(1);
                    Path oldPath = Paths.get(uploadPath, fileName);
                    if (Files.exists(oldPath)) {
                        Files.delete(oldPath);
                        log.info("旧头像已删除: {}", oldPath.toAbsolutePath());
                    }
                }
            } catch (Exception e) {
                // 仅日志打印，不阻断
                log.warn("旧头像删除失败（不影响本次上传），原因：{}", e.getMessage());
            }
        }

        // -----------------------------
        // ⑥ 创建上传目录（不存在自动创建）
        // -----------------------------
        Path dirPath = Paths.get(uploadPath);
        try {
            if (!Files.exists(dirPath)) {
                Files.createDirectories(dirPath);
                log.info("自动创建上传目录: {}", dirPath.toAbsolutePath());
            }
        } catch (IOException e) {
            log.error("创建上传目录失败: {}", e.getMessage());
            return ApiResponse.error(500, "服务器内部错误：无法创建上传目录");
        }

        // -----------------------------
        // ⑦ UUID 生成新文件名，避免重名覆盖
        // -----------------------------
        String newFileName = UUID.randomUUID().toString().replace("-", "") + "." + ext;
        Path targetPath = dirPath.resolve(newFileName);

        try {
            file.transferTo(targetPath.toFile());
            log.info("头像已保存到本地磁盘: {}", targetPath.toAbsolutePath());
        } catch (IOException e) {
            log.error("文件保存失败: {}", e.getMessage());
            return ApiResponse.error(500, "服务器内部错误：头像保存失败");
        }

        // -----------------------------
        // ⑧ 拼接访问 URL 并写入 user.avatar 字段
        //    访问路径：accessPrefix + "/" + 文件名
        // -----------------------------
        String accessUrl = accessPrefix + "/" + newFileName;
        user.setAvatar(accessUrl);
        userRepository.save(user);

        // 成功返回访问路径
        return ApiResponse.success("头像上传成功", accessUrl);
    }

    /**
     * 仅用于联调测试：根据相对路径取磁盘绝对路径
     */
    public String getAbsoluteDiskPath(String fileName) {
        return Paths.get(uploadPath, fileName).toAbsolutePath().toString();
    }
}
