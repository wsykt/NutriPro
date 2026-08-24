package com.health.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.health.config.RestClientConfig;
import com.health.dto.ApiResponse;
import com.health.entity.User;
import com.health.repository.UserRepository;
import com.health.service.AiChatClientService;
import com.health.service.AiConsultService;
import com.health.service.AiContentService;
import com.health.service.AiExerciseService;
import com.health.service.AiNutritionService;
import com.health.service.FamilyRelationService;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/ai")
@CrossOrigin
public class AiConsultController {

    private final UserRepository userRepository;
    private final FamilyRelationService familyRelationService;
    private final AiChatClientService aiChatClientService;
    private final AiConsultService aiConsultService;
    private final AiNutritionService aiNutritionService;
    private final AiExerciseService aiExerciseService;
    private final AiContentService aiContentService;
    private final RestClientConfig restClientConfig;
    private final RestTemplate aiRestTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public AiConsultController(UserRepository userRepository,
                               FamilyRelationService familyRelationService,
                               AiChatClientService aiChatClientService,
                               AiConsultService aiConsultService,
                               AiNutritionService aiNutritionService,
                               AiExerciseService aiExerciseService,
                               AiContentService aiContentService,
                               RestClientConfig restClientConfig,
                               @Qualifier("aiRestTemplate") RestTemplate aiRestTemplate) {
        this.userRepository = userRepository;
        this.familyRelationService = familyRelationService;
        this.aiChatClientService = aiChatClientService;
        this.aiConsultService = aiConsultService;
        this.aiNutritionService = aiNutritionService;
        this.aiExerciseService = aiExerciseService;
        this.aiContentService = aiContentService;
        this.restClientConfig = restClientConfig;
        this.aiRestTemplate = aiRestTemplate;
    }

    private User extractUser(Authentication authentication) {
        if (authentication == null) return null;
        if (authentication.getPrincipal() instanceof User) {
            return (User) authentication.getPrincipal();
        }
        try {
            return userRepository.findByUsername(authentication.getName()).orElse(null);
        } catch (Exception e) {
            return null;
        }
    }

    private int resolveOperateUserId(int currentUserId, Integer targetUserId) {
        if (targetUserId == null || targetUserId == currentUserId) return currentUserId;
        if (familyRelationService.isConfirmedGuardian(currentUserId, targetUserId)) return targetUserId;
        return -1;
    }

    @PostMapping("/consult")
    public ResponseEntity<ApiResponse<Map<String, Object>>> consult(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId,
            @RequestBody Map<String, Object> body) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        int targetId = resolveOperateUserId(current.getUserId(), targetUserId);
        if (targetId == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权操作该用户，请先确认亲属关系"));
        }

        String question = null;
        if (body != null && body.get("question") != null) {
            question = String.valueOf(body.get("question")).trim();
        }
        if (question == null || question.isEmpty()) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(ApiResponse.error(HttpStatus.BAD_REQUEST.value(), "请填写问题"));
        }

        try {
            Map<String, Object> result = aiConsultService.consult(targetId, question);
            return ResponseEntity.ok(ApiResponse.success(result));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error(HttpStatus.INTERNAL_SERVER_ERROR.value(),
                            "AI 咨询失败：" + e.getMessage()));
        }
    }

    @PostMapping("/consult/stream")
    public SseEmitter consultStream(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId,
            @RequestBody Map<String, Object> body) {

        User current = extractUser(authentication);
        SseEmitter emitter = new SseEmitter(120000L);
        if (current == null || current.getUserId() == null) {
            try {
                emitter.send(SseEmitter.event().name("error").data("{\"message\":\"请先登录\"}"));
            } catch (Exception ignore) { }
            emitter.complete();
            return emitter;
        }

        int targetId = resolveOperateUserId(current.getUserId(), targetUserId);
        if (targetId == -1) {
            try {
                emitter.send(SseEmitter.event().name("error").data("{\"message\":\"无权操作该用户，请先确认亲属关系\"}"));
            } catch (Exception ignore) { }
            emitter.complete();
            return emitter;
        }

        String question = null;
        boolean highPerformance = false;
        if (body != null) {
            if (body.get("question") != null) {
                question = String.valueOf(body.get("question")).trim();
            }
            Object hp = body.get("highPerformance");
            highPerformance = hp != null && Boolean.parseBoolean(String.valueOf(hp));
        }
        if (question == null || question.isEmpty()) {
            try {
                emitter.send(SseEmitter.event().name("error").data("{\"message\":\"请填写问题\"}"));
            } catch (Exception ignore) { }
            emitter.complete();
            return emitter;
        }

        aiConsultService.consultStream(emitter, targetId, question, highPerformance);
        return emitter;
    }

    @PostMapping("/voice/parse")
    public ResponseEntity<ApiResponse<Map<String, Object>>> parseVoice(
            Authentication authentication,
            @RequestBody Map<String, Object> body) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        String text = null;
        if (body != null && body.get("text") != null) {
            text = String.valueOf(body.get("text")).trim();
        }
        if (text == null || text.isEmpty()) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(ApiResponse.error(HttpStatus.BAD_REQUEST.value(), "请提供语音文本"));
        }

        try {
            Map<String, Object> result = aiNutritionService.parseVoice(current.getUserId(), text);
            return ResponseEntity.ok(ApiResponse.success(result));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error(HttpStatus.INTERNAL_SERVER_ERROR.value(),
                            "语音解析失败：" + e.getMessage()));
        }
    }

    @PostMapping("/nutrition/analyze")
    public ResponseEntity<ApiResponse<Map<String, Object>>> analyzeNutrition(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        int targetId = resolveOperateUserId(current.getUserId(), targetUserId);
        if (targetId == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权操作该用户，请先确认亲属关系"));
        }

        try {
            Map<String, Object> result = aiNutritionService.analyzeNutrition(targetId);
            return ResponseEntity.ok(ApiResponse.success(result));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error(HttpStatus.INTERNAL_SERVER_ERROR.value(),
                            "营养分析失败：" + e.getMessage()));
        }
    }

    @PostMapping("/food/audit")
    public ResponseEntity<ApiResponse<Map<String, Object>>> auditFood(
            Authentication authentication,
            @RequestBody Map<String, Object> body) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        if (body == null || body.get("food_name") == null) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(ApiResponse.error(HttpStatus.BAD_REQUEST.value(), "请提供食物名称"));
        }

        try {
            Map<String, Object> result = aiNutritionService.auditFood(body);
            return ResponseEntity.ok(ApiResponse.success(result));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error(HttpStatus.INTERNAL_SERVER_ERROR.value(),
                            "食物审核失败：" + e.getMessage()));
        }
    }

    @PostMapping("/report/weekly")
    public ResponseEntity<ApiResponse<Map<String, Object>>> generateWeeklyReport(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        int targetId = resolveOperateUserId(current.getUserId(), targetUserId);
        if (targetId == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权操作该用户，请先确认亲属关系"));
        }

        try {
            Map<String, Object> result = aiContentService.generateWeeklyReport(targetId);
            return ResponseEntity.ok(ApiResponse.success(result));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error(HttpStatus.INTERNAL_SERVER_ERROR.value(),
                            "周报生成失败：" + e.getMessage()));
        }
    }

    @PostMapping("/article/generate")
    public ResponseEntity<ApiResponse<Map<String, Object>>> generateArticle(
            Authentication authentication,
            @RequestBody Map<String, Object> body) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        String topic = null;
        if (body != null && body.get("topic") != null) {
            topic = String.valueOf(body.get("topic")).trim();
        }
        if (topic == null || topic.isEmpty()) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(ApiResponse.error(HttpStatus.BAD_REQUEST.value(), "请提供文章主题"));
        }

        String targetCrowd = body != null ? String.valueOf(body.getOrDefault("target_crowd", "")) : "";

        try {
            Map<String, Object> result = aiContentService.generateArticle(topic, targetCrowd);
            return ResponseEntity.ok(ApiResponse.success(result));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error(HttpStatus.INTERNAL_SERVER_ERROR.value(),
                            "文章生成失败：" + e.getMessage()));
        }
    }

    @PostMapping("/meal/parse")
    public ResponseEntity<ApiResponse<Map<String, Object>>> parseMeal(
            Authentication authentication,
            @RequestBody Map<String, Object> body) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        String text = null;
        if (body != null && body.get("text") != null) {
            text = String.valueOf(body.get("text")).trim();
        }
        if (text == null || text.isEmpty()) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(ApiResponse.error(HttpStatus.BAD_REQUEST.value(), "请提供饮食描述文本"));
        }

        String mealType = body != null ? String.valueOf(body.getOrDefault("meal_type", "")) : "";

        try {
            Map<String, Object> result = aiNutritionService.parseMeal(text, mealType);
            return ResponseEntity.ok(ApiResponse.success(result));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error(HttpStatus.INTERNAL_SERVER_ERROR.value(),
                            "饮食解析失败：" + e.getMessage()));
        }
    }

    @PostMapping("/diet/plan")
    public ResponseEntity<ApiResponse<Map<String, Object>>> generateDietPlan(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId,
            @RequestBody Map<String, Object> body) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        int targetId = resolveOperateUserId(current.getUserId(), targetUserId);
        if (targetId == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权操作该用户，请先确认亲属关系"));
        }

        String goal = body != null ? String.valueOf(body.getOrDefault("goal", "")) : "";

        try {
            Map<String, Object> result = aiNutritionService.generateDietPlan(targetId, goal);
            return ResponseEntity.ok(ApiResponse.success(result));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error(HttpStatus.INTERNAL_SERVER_ERROR.value(),
                            "膳食计划生成失败：" + e.getMessage()));
        }
    }

    @PostMapping("/generate-recipe")
    public ResponseEntity<ApiResponse<String>> generateRecipe(
            Authentication authentication,
            @RequestBody Map<String, Object> request) {

        User user = extractUser(authentication);
        if (user == null || user.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        String prompt = String.valueOf(request.getOrDefault("prompt", ""));
        if (prompt.trim().isEmpty()) {
            return ResponseEntity.badRequest().body(ApiResponse.error(400, "请输入食谱需求"));
        }

        // 构建用户上下文
        StringBuilder userContext = new StringBuilder();
        userContext.append("用户类型：").append(user.getCrowdType() != null ? user.getCrowdType() : "普通用户").append("\n");
        if (user.getAge() != null) userContext.append("年龄：").append(user.getAge()).append("岁\n");
        if (user.getGender() != null) userContext.append("性别：").append(user.getGender()).append("\n");
        if (user.getWeight() != null) userContext.append("体重：").append(user.getWeight()).append("kg\n");
        if (user.getHeight() != null) userContext.append("身高：").append(user.getHeight()).append("cm\n");
        if (user.getAllergicFoods() != null && !user.getAllergicFoods().trim().isEmpty())
            userContext.append("过敏食材：").append(user.getAllergicFoods()).append("\n");
        if (user.getDietaryRestrictions() != null && !user.getDietaryRestrictions().trim().isEmpty())
            userContext.append("饮食限制：").append(user.getDietaryRestrictions()).append("\n");
        if (user.getTastePreference() != null && !user.getTastePreference().trim().isEmpty() &&
                !"清淡".equals(user.getTastePreference()))
            userContext.append("口味偏好：").append(user.getTastePreference()).append("\n");

        // 更完善的系统提示，包含烹饪步骤，去除图片相关
        String systemPrompt = "你是一位专业营养师，请根据用户需求生成一份健康食谱。\n\n" +
                "【用户信息】\n" + userContext.toString() + "\n" +
                "【用户需求】" + prompt + "\n\n" +
                "请严格按以下JSON格式输出（不要包含markdown代码块标记，仅输出纯JSON）：\n" +
                "{\n" +
                "  \"name\": \"食谱名称\",\n" +
                "  \"description\": \"简短描述\",\n" +
                "  \"calories\": 总热量(整数),\n" +
                "  \"protein\": 蛋白质克数(整数),\n" +
                "  \"fat\": 脂肪克数(整数),\n" +
                "  \"carbs\": 碳水化合物克数(整数),\n" +
                "  \"fiber\": 膳食纤维克数(整数),\n" +
                "  \"tags\": [\"标签1\", \"标签2\"],\n" +
                "  \"ingredients\": [\n" +
                "    {\"ingredient_name\": \"食材名\", \"amount\": 用量, \"unit\": \"单位\"}\n" +
                "  ],\n" +
                "  \"steps\": [\"步骤1描述\", \"步骤2描述\", \"步骤3描述\"]\n" +
                "}\n" +
                "注意：营养素单位为每份克数，热量为kcal。" +
                "tags中至少包含1个与用户类型匹配的标签。" +
                "确保食材适合该用户（如过敏、饮食限制等）。\n";

        try {
            String reply = aiChatClientService.callRecipeApi(systemPrompt, prompt);
            return ResponseEntity.ok(ApiResponse.success(reply));
        } catch (Exception e) {
            // 安全加固：不再兜底返回假食谱（避免把 AI 失败伪装成成功结果误导用户），
            // 如实返回错误（含熔断提示），由前端展示失败状态。
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY)
                    .body(ApiResponse.error(HttpStatus.BAD_GATEWAY.value(), "AI生成食谱失败：" + e.getMessage()));
        }
    }

    @PostMapping("/recipe/recommend")
    public ResponseEntity<ApiResponse<Map<String, Object>>> recommendRecipe(
            Authentication authentication,
            @RequestBody Map<String, Object> body) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        try {
            Map<String, Object> result = aiNutritionService.recommendRecipe(current.getUserId(), body);
            return ResponseEntity.ok(ApiResponse.success(result));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error(HttpStatus.INTERNAL_SERVER_ERROR.value(),
                            "菜谱推荐失败：" + e.getMessage()));
        }
    }

    @PostMapping("/exercise/advice")
    public ResponseEntity<ApiResponse<Map<String, Object>>> adviseExercise(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId,
            @RequestBody Map<String, Object> body) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        int targetId = resolveOperateUserId(current.getUserId(), targetUserId);
        if (targetId == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权操作该用户，请先确认亲属关系"));
        }

        try {
            Map<String, Object> result = aiExerciseService.adviseExercise(targetId, body);
            return ResponseEntity.ok(ApiResponse.success(result));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error(HttpStatus.INTERNAL_SERVER_ERROR.value(),
                            "运动建议生成失败：" + e.getMessage()));
        }
    }

    /**
     * 本地知识库检索：供前端 AI 分析周报/月报时，按营养问题（蛋白质超标/碳水不足等）检索知识卡片，
     * 将命中内容注入提示词后发给大模型。透传调用 AI 服务 /api/v1/retrieve。
     */
    @PostMapping("/knowledge/retrieve")
    public ResponseEntity<ApiResponse<Map<String, Object>>> retrieveKnowledge(
            Authentication authentication,
            @RequestBody Map<String, Object> body) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        String query = body != null ? String.valueOf(body.getOrDefault("query", "")).trim() : "";
        if (query.isEmpty()) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(ApiResponse.error(HttpStatus.BAD_REQUEST.value(), "请提供检索关键词"));
        }
        int topK = 3;
        if (body != null && body.get("top_k") != null) {
            try { topK = Integer.parseInt(String.valueOf(body.get("top_k"))); } catch (Exception ignore) { }
        }
        if (topK < 1 || topK > 10) topK = 3;
        String crowd = body != null ? String.valueOf(body.getOrDefault("target_crowd", "")) : "";

        try {
            Map<String, Object> requestBody = new LinkedHashMap<>();
            requestBody.put("query", query);
            requestBody.put("top_k", topK);
            requestBody.put("target_crowd", crowd);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            ResponseEntity<String> resp = aiRestTemplate.postForEntity(
                    restClientConfig.getAiBaseUrl() + "/retrieve", entity, String.class);
            Map<String, Object> aiResult = objectMapper.readValue(resp.getBody(), Map.class);

            // 精简透传：只保留 content 与来源，控制响应体积
            List<Map<String, Object>> items = new ArrayList<>();
            Object rawResults = aiResult.get("results");
            if (rawResults instanceof List) {
                for (Object o : (List<?>) rawResults) {
                    if (!(o instanceof Map)) continue;
                    Map<?, ?> m = (Map<?, ?>) o;
                    Object content = m.get("content");
                    if (content == null || String.valueOf(content).trim().isEmpty()) continue;
                    Map<String, Object> item = new LinkedHashMap<>();
                    item.put("content", String.valueOf(content).trim());
                    Object meta = m.get("metadata");
                    String source = "";
                    if (meta instanceof Map) {
                        Object s = ((Map<?, ?>) meta).get("source");
                        if (s != null) source = String.valueOf(s);
                    }
                    item.put("source", source);
                    items.add(item);
                }
            }

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("query", query);
            result.put("total", items.size());
            result.put("results", items);
            return ResponseEntity.ok(ApiResponse.success(result));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(ApiResponse.error(HttpStatus.INTERNAL_SERVER_ERROR.value(),
                            "知识库检索失败：" + e.getMessage()));
        }
    }
}
