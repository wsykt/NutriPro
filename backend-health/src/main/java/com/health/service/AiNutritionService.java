package com.health.service;

import com.health.entity.User;
import com.health.repository.UserRepository;
import com.health.util.CircuitBreaker;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * AI 饮食营养域：语音解析 / 营养分析 / 食物审核 / 饮食解析 / 膳食计划 / 菜谱推荐。
 *
 * 从原 AiChatService 拆分出的「饮食营养域」：
 * - parseVoice：语音转文本结构（营养数据录入入口）
 * - analyzeNutrition：基于今日饮食+运动+身体数据的营养分析
 * - auditFood：食物健康审核
 * - parseMeal：一句话饮食解析（结构化）
 * - generateDietPlan：膳食计划（复用完整健康快照）
 * - recommendRecipe：菜谱推荐（复用完整健康快照）
 *
 * 所有对外 HTTP 调用统一走 AiChatClientService（共享熔断器，避免重复实现）。
 */
@Slf4j
@Service
public class AiNutritionService {

    private final CircuitBreaker circuitBreaker;
    private final UserRepository userRepository;
    private final AiChatContextBuilder contextBuilder;
    private final AiChatClientService aiChatClient;

    public AiNutritionService(CircuitBreaker circuitBreaker,
                              UserRepository userRepository,
                              AiChatContextBuilder contextBuilder,
                              AiChatClientService aiChatClient) {
        this.circuitBreaker = circuitBreaker;
        this.userRepository = userRepository;
        this.contextBuilder = contextBuilder;
        this.aiChatClient = aiChatClient;
    }

    /** 语音解析：把用户语音文本转成结构化饮食数据 */
    public Map<String, Object> parseVoice(Integer userId, String text) {
        if (circuitBreaker.isOpen()) {
            log.warn("AI服务熔断保护中，跳过语音解析调用");
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", circuitBreaker.buildBreakerMessage());
            return errorMap;
        }
        Map<String, Object> requestBody = new LinkedHashMap<>();
        requestBody.put("text", text);
        return aiChatClient.postForMap("/voice/parse", requestBody, "语音解析");
    }

    /** 营养分析：结合今日饮食 + 近7日运动 + 身体指标趋势 */
    public Map<String, Object> analyzeNutrition(Integer userId) {
        if (circuitBreaker.isOpen()) {
            log.warn("AI服务熔断保护中，跳过营养分析调用");
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", circuitBreaker.buildBreakerMessage());
            return errorMap;
        }
        User user = userRepository.findById(userId).orElse(null);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }

        String today = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);
        Map<String, Object> snapshot = contextBuilder.buildHealthSnapshot(user, today);

        Map<String, Object> requestBody = new LinkedHashMap<>();
        requestBody.put("user_profile", snapshot.get("profile"));
        requestBody.put("daily_nutrition", snapshot.get("today_diet_total"));
        // 近 7 日运动数据（v2.0：营养分析必须参考运动消耗）
        requestBody.put("daily_exercise", snapshot.get("recent_exercise"));
        requestBody.put("body_metrics_trend", snapshot.get("body_metrics_trend"));
        requestBody.put("today_body_metrics", snapshot.get("today_body_metrics"));

        return aiChatClient.postForMap("/nutrition/analyze", requestBody, "营养分析");
    }

    /** 食物健康审核：对录入的食物数据进行合规/健康度检查 */
    public Map<String, Object> auditFood(Map<String, Object> foodData) {
        if (circuitBreaker.isOpen()) {
            log.warn("AI服务熔断保护中，跳过食物审核调用");
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", circuitBreaker.buildBreakerMessage());
            return errorMap;
        }
        return aiChatClient.postForMap("/food/audit", foodData, "食物审核");
    }

    /** 一句话饮食解析：把自然语言饮食描述转成结构化餐食记录 */
    public Map<String, Object> parseMeal(String text, String mealType) {
        if (circuitBreaker.isOpen()) {
            log.warn("AI服务熔断保护中，跳过饮食解析调用");
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", circuitBreaker.buildBreakerMessage());
            return errorMap;
        }
        Map<String, Object> requestBody = new LinkedHashMap<>();
        requestBody.put("text", text);
        if (mealType != null && !mealType.isEmpty()) {
            requestBody.put("meal_type", mealType);
        }
        return aiChatClient.postForMap("/meal/parse", requestBody, "饮食解析");
    }

    /** 膳食计划：基于目标与完整健康快照生成一日三餐方案 */
    public Map<String, Object> generateDietPlan(Integer userId, String goal) {
        if (circuitBreaker.isOpen()) {
            log.warn("AI服务熔断保护中，跳过膳食计划生成调用");
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", circuitBreaker.buildBreakerMessage());
            return errorMap;
        }
        User user = userRepository.findById(userId).orElse(null);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }

        String today = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);
        // 构建完整健康快照（含身体数据+运动数据+饮食数据）
        Map<String, Object> snapshot = contextBuilder.buildHealthSnapshot(user, today);

        Map<String, Object> requestBody = new LinkedHashMap<>();
        requestBody.put("user_profile", snapshot.get("profile"));
        requestBody.put("goal", goal);
        // v2.0：膳食计划必须同时参考身体数据与运动数据
        requestBody.put("today_body_metrics", snapshot.get("today_body_metrics"));
        requestBody.put("body_metrics_trend", snapshot.get("body_metrics_trend"));
        requestBody.put("recent_exercise", snapshot.get("recent_exercise"));
        requestBody.put("today_diet", snapshot.get("today_diet"));
        requestBody.put("today_diet_total", snapshot.get("today_diet_total"));
        requestBody.put("diet_reference", snapshot.get("diet_reference"));

        return aiChatClient.postForMap("/diet/plan", requestBody, "膳食计划生成");
    }

    /** 菜谱推荐：复用健康快照，供 ai_service 自动推导热量需求/运动水平 */
    public Map<String, Object> recommendRecipe(Integer userId, Map<String, Object> body) {
        if (circuitBreaker.isOpen()) {
            log.warn("AI服务熔断保护中，跳过菜谱推荐调用");
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", circuitBreaker.buildBreakerMessage());
            return errorMap;
        }
        User user = userRepository.findById(userId).orElse(null);
        if (user != null) {
            // 复用健康快照，供 ai_service 自动推导热量需求/运动水平，无需用户重复说明
            String today = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);
            Map<String, Object> snapshot = contextBuilder.buildHealthSnapshot(user, today);
            body.put("user_profile", snapshot.get("profile"));
            body.put("today_body_metrics", snapshot.get("today_body_metrics"));
            body.put("body_metrics_trend", snapshot.get("body_metrics_trend"));
            body.put("recent_exercise", snapshot.get("recent_exercise"));
            body.put("today_diet", snapshot.get("today_diet"));
            body.put("today_diet_total", snapshot.get("today_diet_total"));
            body.put("diet_reference", snapshot.get("diet_reference"));
        }
        return aiChatClient.postForMap("/food/recommend", body, "菜谱推荐");
    }
}
