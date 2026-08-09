package com.health.service;

import com.health.entity.User;
import com.health.repository.UserRepository;
import com.health.util.CircuitBreaker;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * AI 内容生成域：周报 / 科普文章。
 *
 * 从原 AiChatService 拆分出的「内容域」：
 * - generateWeeklyReport：周报生成
 * - generateArticle：科普文章生成
 *
 * 文章母稿生成（generateArticleMotherDraft）属于 /chat 端点 HTTP 通信，
 * 已下沉至 AiChatClientService，供 ArticleService 复用。
 */
@Slf4j
@Service
public class AiContentService {

    private final CircuitBreaker circuitBreaker;
    private final UserRepository userRepository;
    private final AiChatClientService aiChatClient;

    public AiContentService(CircuitBreaker circuitBreaker,
                            UserRepository userRepository,
                            AiChatClientService aiChatClient) {
        this.circuitBreaker = circuitBreaker;
        this.userRepository = userRepository;
        this.aiChatClient = aiChatClient;
    }

    /** 生成周报 */
    public Map<String, Object> generateWeeklyReport(Integer userId) {
        if (circuitBreaker.isOpen()) {
            log.warn("AI服务熔断保护中，跳过周报生成调用");
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", circuitBreaker.buildBreakerMessage());
            return errorMap;
        }
        User user = userRepository.findById(userId).orElse(null);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }

        Map<String, Object> requestBody = new LinkedHashMap<>();
        Map<String, Object> userProfile = new LinkedHashMap<>();
        userProfile.put("username", user.getUsername());
        userProfile.put("gender", user.getGender());
        userProfile.put("age", user.getAge());
        userProfile.put("height", user.getHeight());
        userProfile.put("weight", user.getWeight());
        userProfile.put("crowd_type", user.getCrowdType());
        requestBody.put("user_profile", userProfile);
        requestBody.put("weekly_stats", new LinkedHashMap<>());

        return aiChatClient.postForMap("/report/weekly-summary", requestBody, "周报生成");
    }

    /** 生成科普文章 */
    public Map<String, Object> generateArticle(String topic, String targetCrowd) {
        if (circuitBreaker.isOpen()) {
            log.warn("AI服务熔断保护中，跳过文章生成调用");
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", circuitBreaker.buildBreakerMessage());
            return errorMap;
        }
        Map<String, Object> requestBody = new LinkedHashMap<>();
        requestBody.put("topic", topic);
        requestBody.put("target_crowd", targetCrowd);

        return aiChatClient.postForMap("/article/generate", requestBody, "文章生成");
    }
}
