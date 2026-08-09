package com.health.service;

import com.health.config.RestClientConfig;
import com.health.util.CircuitBreaker;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * AI 服务 HTTP 客户端：封装对 Python AI 服务（FastAPI :8002）的调用。
 *
 * 从原 AiChatService 拆分出的「HTTP 通信域」：
 * - postForMap：通用 POST 调用（熔断检查 + 空响应 + 错误文案包装），供各业务服务复用
 * - callAiService / callRecipeApi：/chat 编排层特殊调用（返回文本，错误时抛出）
 * - escapeJson / readAll：SSE 透传辅助
 *
 * 职责单一：只负责与 AI 服务的网络通信，不做任何业务数据组装。
 */
@Slf4j
@Service
public class AiChatClientService {

    private final CircuitBreaker circuitBreaker;
    private final RestClientConfig restClientConfig;
    private final ObjectMapper objectMapper;

    @Autowired
    @Qualifier("aiRestTemplate")
    private RestTemplate restTemplate;

    public AiChatClientService(CircuitBreaker circuitBreaker, RestClientConfig restClientConfig) {
        this.circuitBreaker = circuitBreaker;
        this.restClientConfig = restClientConfig;
        this.objectMapper = new ObjectMapper();
    }

    public CircuitBreaker getCircuitBreaker() {
        return circuitBreaker;
    }

    public RestClientConfig getRestClientConfig() {
        return restClientConfig;
    }

    public ObjectMapper getObjectMapper() {
        return objectMapper;
    }

    /**
     * 通用 POST 调用 AI 服务（带熔断保护），返回解析后的 Map。
     *
     * 熔断打开时直接返回错误文案 Map（不发起请求）；
     * 调用失败时返回「{@code errorLabel}失败: ...」错误 Map（与拆分前行为一致）。
     *
     * @param path         AI 服务相对路径（如 /voice/parse）
     * @param requestBody  请求体
     * @param errorLabel   错误前缀（如「语音解析」）
     */
    public Map<String, Object> postForMap(String path, Map<String, Object> requestBody, String errorLabel) {
        if (circuitBreaker.isOpen()) {
            log.warn("AI服务熔断保护中，跳过{}调用", errorLabel);
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", circuitBreaker.buildBreakerMessage());
            return errorMap;
        }
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            ResponseEntity<String> response = restTemplate.postForEntity(
                    restClientConfig.getAiBaseUrl() + path, entity, String.class);

            if (response.getBody() == null) {
                throw new RuntimeException("AI 服务返回空响应");
            }

            Map<String, Object> result = objectMapper.readValue(response.getBody(), Map.class);
            circuitBreaker.recordSuccess();
            return result;
        } catch (Exception e) {
            circuitBreaker.recordFailure();
            log.error("AI服务调用失败: {}", e.getMessage(), e);
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", errorLabel + "失败: " + e.getMessage());
            return errorMap;
        }
    }

    /**
     * 调用 AI 服务 /chat 端点生成科普文章母稿（带 【#TAG#】 标记的文本）。
     * 错误时抛出异常（由调用方决定如何处理），与拆分前行为一致。
     */
    public String generateArticleMotherDraft(String prompt) {
        log.info("开始生成文章母稿, promptSize={}", prompt != null ? prompt.length() : 0);
        if (circuitBreaker.isOpen()) {
            log.warn("AI服务熔断保护中，跳过文章母稿生成");
            throw new RuntimeException(circuitBreaker.buildBreakerMessage());
        }
        try {
            Map<String, Object> requestBody = new LinkedHashMap<>();
            requestBody.put("message", prompt);
            requestBody.put("user_id", 0);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            ResponseEntity<String> response = restTemplate.postForEntity(
                    restClientConfig.getAiBaseUrl() + "/chat", entity, String.class);

            if (response.getBody() == null) {
                throw new RuntimeException("AI 服务返回空响应");
            }

            Map<String, Object> responseMap = objectMapper.readValue(response.getBody(), Map.class);
            String content = (String) responseMap.get("response");
            circuitBreaker.recordSuccess();
            log.info("文章母稿生成完成, contentSize={}", content != null ? content.length() : 0);
            return content != null ? content : "";
        } catch (Exception e) {
            circuitBreaker.recordFailure();
            log.error("AI服务调用失败: {}", e.getMessage(), e);
            throw new RuntimeException("调用 AI 生成母稿失败: " + e.getMessage(), e);
        }
    }

    /**
     * 调用 AI 服务编排层生成食谱（走 Agent 编排层，享受知识库检索+记忆+降级）。
     * 错误时抛出异常（由调用方决定如何处理），与拆分前行为一致。
     */
    public String callRecipeApi(String systemPrompt, String userQuestion) {
        if (circuitBreaker.isOpen()) {
            log.warn("AI服务熔断保护中，跳过食谱生成调用");
            throw new RuntimeException(circuitBreaker.buildBreakerMessage());
        }
        try {
            Map<String, Object> requestBody = new LinkedHashMap<>();
            requestBody.put("message", systemPrompt + "\n\n" + userQuestion);
            requestBody.put("user_id", 0);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            ResponseEntity<String> response = restTemplate.postForEntity(
                    restClientConfig.getAiBaseUrl() + "/chat", entity, String.class);

            if (response.getBody() == null) {
                throw new RuntimeException("AI 服务返回空响应");
            }

            Map<String, Object> responseMap = objectMapper.readValue(response.getBody(), Map.class);
            String content = (String) responseMap.get("response");
            circuitBreaker.recordSuccess();
            return content != null ? content : "未返回有效内容";

        } catch (Exception e) {
            circuitBreaker.recordFailure();
            throw new RuntimeException("调用AI服务生成食谱失败: " + e.getMessage(), e);
        }
    }

    /**
     * 调用 AI 服务 /chat 端点（普通健康咨询，无 SSE），返回回复文本。
     *
     * 与通用 postForMap 不同：本方法返回纯文本回复，并对「连接拒绝 / 超时」给出
     * 面向用户的友好提示（与拆分前行为一致）；错误不抛出。
     */
    public String callAiService(Integer userId, String question, Map<String, Object> healthSnapshot, String systemPrompt) {
        // 断路器检查：熔断时快速失败
        if (circuitBreaker.isOpen()) {
            log.warn("AI服务熔断保护中，跳过健康咨询调用");
            return circuitBreaker.buildBreakerMessage();
        }

        try {
            Map<String, Object> requestBody = new LinkedHashMap<>();
            requestBody.put("message", question);
            requestBody.put("user_id", userId);
            requestBody.put("health_snapshot", healthSnapshot);
            // 携带 Java 侧构建的系统提示词（v2.0：综合身体数据+运动数据）
            if (systemPrompt != null && !systemPrompt.isEmpty()) {
                requestBody.put("system_prompt", systemPrompt);
            }

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            ResponseEntity<String> response = restTemplate.postForEntity(
                    restClientConfig.getAiBaseUrl() + "/chat", entity, String.class);

            if (response.getBody() == null) {
                throw new RuntimeException("AI 服务返回空响应");
            }

            Map<String, Object> responseMap = objectMapper.readValue(response.getBody(), Map.class);
            String reply = (String) responseMap.get("response");
            circuitBreaker.recordSuccess();
            return reply != null ? reply : "未返回有效内容";

        } catch (Exception e) {
            circuitBreaker.recordFailure();
            log.error("AI服务调用失败: {}", e.getMessage(), e);
            String errorMsg = e.getMessage();
            if (errorMsg != null && errorMsg.contains("Connection refused")) {
                return "⚠️ AI 服务未启动，请先启动 Python AI 服务（端口 8002）。";
            }
            if (errorMsg != null && errorMsg.contains("timeout")) {
                return "⚠️ AI 服务响应超时，请稍后重试。";
            }
            return "⚠️ AI 回复失败：" + (errorMsg != null ? errorMsg : "未知错误")
                    + "\n\n如问题持续，请检查 AI 服务是否正常运行。";
        }
    }

    /** 简单 JSON 字符串转义，防止错误消息破坏 SSE data 格式 */
    public String escapeJson(String s) {
        if (s == null) return "";
        return s.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\n", "\\n").replace("\r", "\\r");
    }

    /** 读取输入流全部字节 */
    public byte[] readAll(java.io.InputStream in) throws Exception {
        java.io.ByteArrayOutputStream buffer = new java.io.ByteArrayOutputStream();
        byte[] chunk = new byte[4096];
        int n;
        while ((n = in.read(chunk)) != -1) {
            buffer.write(chunk, 0, n);
        }
        return buffer.toByteArray();
    }
}
