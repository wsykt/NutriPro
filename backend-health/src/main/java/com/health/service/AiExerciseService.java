package com.health.service;

import com.health.entity.User;
import com.health.repository.UserRepository;
import com.health.util.CircuitBreaker;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * AI 个性化运动域：adviseExercise。
 *
 * 从原 AiChatService 拆分出的「运动域」：基于用户身体指标、近7日运动数据、
 * 今日饮食与运动偏好，生成个性化运动方案。
 */
@Slf4j
@Service
public class AiExerciseService {

    private final CircuitBreaker circuitBreaker;
    private final UserRepository userRepository;
    private final AiChatContextBuilder contextBuilder;
    private final AiChatClientService aiChatClient;

    public AiExerciseService(CircuitBreaker circuitBreaker,
                             UserRepository userRepository,
                             AiChatContextBuilder contextBuilder,
                             AiChatClientService aiChatClient) {
        this.circuitBreaker = circuitBreaker;
        this.userRepository = userRepository;
        this.contextBuilder = contextBuilder;
        this.aiChatClient = aiChatClient;
    }

    /** 个性化运动方案：结合身体指标 + 运动数据 + 运动偏好 */
    public Map<String, Object> adviseExercise(Integer userId, Map<String, Object> body) {
        if (circuitBreaker.isOpen()) {
            log.warn("AI服务熔断保护中，跳过运动建议调用");
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", circuitBreaker.buildBreakerMessage());
            return errorMap;
        }
        User user = userRepository.findById(userId).orElse(null);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }

        Map<String, Object> requestBody = new LinkedHashMap<>();

        // 复用健康快照（含身高/体重/BMI/人群/今日饮食/近7日运动），
        // 供 ai_service 自动推导热量需求与运动水平分级，无需用户重复说明
        String today = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);
        Map<String, Object> snapshot = contextBuilder.buildHealthSnapshot(user, today);
        requestBody.put("user_profile", snapshot.get("profile"));
        requestBody.put("goal", body.getOrDefault("goal", "保持健康"));
        requestBody.put("preferences", body.getOrDefault("preferences", ""));
        requestBody.put("chronic_diseases", body.getOrDefault("chronic_diseases", new ArrayList<>()));
        requestBody.put("today_body_metrics", snapshot.get("today_body_metrics"));
        requestBody.put("recent_exercise", snapshot.get("recent_exercise"));
        requestBody.put("today_diet", snapshot.get("today_diet"));
        requestBody.put("today_diet_total", snapshot.get("today_diet_total"));
        requestBody.put("body_metrics_trend", snapshot.get("body_metrics_trend"));
        requestBody.put("diet_reference", snapshot.get("diet_reference"));

        return aiChatClient.postForMapLong("/exercise/advice", requestBody, "运动建议生成");
    }
}
