package com.health.controller;

import com.health.dto.ApiResponse;
import com.health.entity.User;
import com.health.repository.UserRepository;
import com.health.service.AiChatService;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@RestController
@RequestMapping("/api/ai")
@CrossOrigin
public class AiChatController {

    private final UserRepository userRepository;
    private final AiChatService aiChatService;
    private final ExecutorService executorService = Executors.newCachedThreadPool();

    public AiChatController(UserRepository userRepository, AiChatService aiChatService) {
        this.userRepository = userRepository;
        this.aiChatService = aiChatService;
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

    @GetMapping("/chat-stream")
    public SseEmitter chatStream(
            Authentication authentication,
            @RequestParam String message) {

        SseEmitter emitter = new SseEmitter(300000L);

        executorService.execute(() -> {
            try {
                User user = extractUser(authentication);
                String userInfo = user != null ? user.getCrowdType() : "普通用户";

                String systemPrompt = "你是一位专业的健康助手，专门提供饮食、运动、营养方面的建议。\n" +
                        "用户类型：" + userInfo + "\n" +
                        "请用中文回答，条理清晰，适当使用Markdown格式。";

                aiChatService.streamConsult(user != null ? user.getUserId() : null, systemPrompt, message, emitter);

            } catch (Exception e) {
                try {
                    emitter.send(SseEmitter.event()
                            .name("error")
                            .data("AI回复失败：" + e.getMessage()));
                } catch (IOException ignored) {}
                emitter.completeWithError(e);
            }
        });

        return emitter;
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

        String userInfo = user.getCrowdType() != null ? user.getCrowdType() : "普通用户";
        
        String systemPrompt = "你是一位专业营养师，请根据用户需求生成健康食谱，严格按以下JSON格式输出（不要包含markdown代码块标记）：\n" +
                "{\n" +
                "  \"name\": \"食谱名称\",\n" +
                "  \"description\": \"简短描述及烹饪步骤\",\n" +
                "  \"calories\": 数字,\n" +
                "  \"protein\": 数字,\n" +
                "  \"fat\": 数字,\n" +
                "  \"carbs\": 数字,\n" +
                "  \"fiber\": 数字,\n" +
                "  \"tags\": [\"标签1\",\"标签2\"],\n" +
                "  \"ingredients\": [{\"ingredient_name\":\"食材名\",\"amount\":数字,\"unit\":\"g或ml或个\"}]\n" +
                "}\n" +
                "营养素单位为每份克数，热量为kcal。\n\n" +
                "用户类型：" + userInfo + "\n";

        try {
            String reply = aiChatService.callRecipeApi(systemPrompt, prompt);
            return ResponseEntity.ok(ApiResponse.success(reply));
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.ok(ApiResponse.success("{\n" +
                    "  \"name\": \"健康蔬菜沙拉\",\n" +
                    "  \"description\": \"清爽低卡的蔬菜沙拉，富含维生素和膳食纤维\",\n" +
                    "  \"calories\": 180,\n" +
                    "  \"protein\": 12,\n" +
                    "  \"fat\": 8,\n" +
                    "  \"carbs\": 15,\n" +
                    "  \"fiber\": 6,\n" +
                    "  \"tags\": [\"减脂\", \"低卡\", \"均衡\"],\n" +
                    "  \"ingredients\": [\n" +
                    "    {\"ingredient_name\": \"生菜\", \"amount\": 100, \"unit\": \"g\"},\n" +
                    "    {\"ingredient_name\": \"番茄\", \"amount\": 100, \"unit\": \"g\"},\n" +
                    "    {\"ingredient_name\": \"鸡胸肉\", \"amount\": 50, \"unit\": \"g\"},\n" +
                    "    {\"ingredient_name\": \"橄榄油\", \"amount\": 10, \"unit\": \"ml\"},\n" +
                    "    {\"ingredient_name\": \"沙拉酱\", \"amount\": 20, \"unit\": \"g\"}\n" +
                    "  ]\n" +
                    "}"));
        }
    }

    @GetMapping("/generate-recipe-stream")
    public SseEmitter generateRecipeStream(
            Authentication authentication,
            @RequestParam String prompt) {

        SseEmitter emitter = new SseEmitter(300000L);

        executorService.execute(() -> {
            try {
                User user = extractUser(authentication);

                String systemPrompt = "你是一位专业营养师，请根据用户需求生成健康食谱，严格按JSON格式输出，不要包含markdown代码块标记。";

                aiChatService.streamConsult(user != null ? user.getUserId() : null, systemPrompt, prompt, emitter);

            } catch (Exception e) {
                try {
                    emitter.send(SseEmitter.event()
                            .name("error")
                            .data("AI回复失败：" + e.getMessage()));
                } catch (IOException ignored) {}
                emitter.completeWithError(e);
            }
        });

        return emitter;
    }
}