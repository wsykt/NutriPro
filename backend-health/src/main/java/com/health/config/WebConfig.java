package com.health.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * Web MVC 配置类
 * 功能：静态资源映射，把浏览器 URL（/uploads/avatar/**） 映射到服务器本地磁盘目录
 * 这样前端可以直接用：http://localhost:8082/uploads/avatar/xxx.png 来访问头像图片
 *
 * 注意：使用 file: 前缀 + 绝对路径（带 trailing /）才能正确映射到磁盘文件
 */
@Configuration
public class WebConfig implements WebMvcConfigurer {

    /** 本地磁盘存储路径（来自 application.yml upload.path） */
    @Value("${upload.path}")
    private String uploadPath;

    /** URL 访问前缀（来自 application.yml upload.access-prefix） */
    @Value("${upload.access-prefix}")
    private String accessPrefix;

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // 规范化：末尾补齐 / ，避免 file:/d:/xxx + yyy.png 拼错
        String path = uploadPath.endsWith("/") ? uploadPath : uploadPath + "/";
        String prefix = accessPrefix.endsWith("/") ? accessPrefix : accessPrefix + "/";

        registry.addResourceHandler(prefix + "**")
                // "file:" 前缀代表从磁盘加载资源
                .addResourceLocations("file:" + path);
    }
}
