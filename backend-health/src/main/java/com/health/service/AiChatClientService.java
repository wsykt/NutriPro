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
import java.util.List;
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

    @Autowired
    @Qualifier("aiRestTemplateLong")
    private RestTemplate restTemplateLong;

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
    /**
     * 普通用户链路统一走本方法：返回前剥离管理员端元数据（_meta 决策链 / tokens 消耗明细），
     * 保证用户看不到后端流水线信息（成功/失败断点、token 消耗、耗时），只有管理员流水线可见。
     */
    public Map<String, Object> postForMap(String path, Map<String, Object> requestBody, String errorLabel) {
        return postForMap(path, requestBody, errorLabel, false, false);
    }

    /**
     * 长耗时版 postForMap：运动建议等需本地 Ollama 推理的功能使用 300s 长超时模板，
     * 避免 30s socket 超时导致本地 LLM 生成中途断开。同样剥离管理员端元数据。
     */
    public Map<String, Object> postForMapLong(String path, Map<String, Object> requestBody, String errorLabel) {
        return postForMap(path, requestBody, errorLabel, true, false);
    }

    /**
     * 管理员流水线专用：保留完整响应（含 _meta.trace / tokens），供 AiPipelineController 展开断点与展示 token。
     */
    public Map<String, Object> postForMapKeepMeta(String path, Map<String, Object> requestBody, String errorLabel) {
        return postForMap(path, requestBody, errorLabel, false, true);
    }

    /**
     * 管理员流水线专用（长超时版）：保留完整响应（含 _meta.trace / tokens）。
     */
    public Map<String, Object> postForMapLongKeepMeta(String path, Map<String, Object> requestBody, String errorLabel) {
        return postForMap(path, requestBody, errorLabel, true, true);
    }

    private Map<String, Object> postForMap(String path, Map<String, Object> requestBody, String errorLabel,
                                           boolean useLongTimeout, boolean keepAdminMeta) {
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

            ResponseEntity<String> response = (useLongTimeout ? restTemplateLong : restTemplate).postForEntity(
                    restClientConfig.getAiBaseUrl() + path, entity, String.class);

            if (response.getBody() == null) {
                throw new RuntimeException("AI 服务返回空响应");
            }

            Map<String, Object> result = objectMapper.readValue(response.getBody(), Map.class);
            circuitBreaker.recordSuccess();
            if (!keepAdminMeta) {
                stripAdminMeta(result);
            }
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
     * 剥离管理员端元数据：移除 AI 服务响应中供管理员流水线展示的内部信息
     * （_meta 决策链 trace/route/mode/timing、token 消耗明细、provider 来源、耗时、检索明细、校验结果）。
     * 普通用户只保留业务字段（conversation_id / response / meal_plan 等）。
     */
    @SuppressWarnings("unchecked")
    private void stripAdminMeta(Map<String, Object> result) {
        if (result == null) return;
        result.remove("_meta");
        Object dataObj = result.get("data");
        if (dataObj instanceof Map) {
            Map<String, Object> data = (Map<String, Object>) dataObj;
            data.remove("tokens");
            data.remove("_meta");
            data.remove("route");
            data.remove("mode");
            data.remove("provider");
            data.remove("validation");
            data.remove("elapsed_seconds");
            data.remove("retrieve_info");
            data.remove("timing_breakdown");
            data.remove("high_performance");
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
            // 母稿为带标记的完整 prompt，走 AI 服务透传通道（_raw_prompt），避免被健康咨询管线重新包装导致标记丢失
            requestBody.put("_raw_prompt", true);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            // 母稿生成属长文本任务，使用 300s 长超时模板（本地 Ollama 生成长文可能超过 30s）
            ResponseEntity<String> response = restTemplateLong.postForEntity(
                    restClientConfig.getAiBaseUrl() + "/chat", entity, String.class);

            if (response.getBody() == null) {
                throw new RuntimeException("AI 服务返回空响应");
            }

            Map<String, Object> responseMap = objectMapper.readValue(response.getBody(), Map.class);
            // AI 服务统一响应结构：{success, code, message, data:{response,...}}，正文在 data.response
            String content = null;
            Object dataObj = responseMap.get("data");
            if (dataObj instanceof Map) {
                Object resp = ((Map<?, ?>) dataObj).get("response");
                content = resp != null ? String.valueOf(resp) : null;
            }
            if (content == null) {
                // 兼容旧的顶层 response 字段
                Object topResp = responseMap.get("response");
                if (topResp != null) {
                    content = String.valueOf(topResp);
                }
            }
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
     * 调用 AI 服务 /articles/mother-draft 端点生成科普文章母稿（B方案双模型流水线）。
     * <p>后端只传 topic 与目标人群，母稿由 AI 服务内 pipeline_v32 完成三阶段：
     * 本地 Ollama 出框架 → 云端 DeepSeek 外扩 → 本地格式校验（含五道质量闸门）。
     * 错误时抛出异常（由调用方决定如何处理）。
     */
    public String generateArticleMotherDraftB(String topic, String persona) {
        return generateArticleMotherDraftB(topic, persona, null);
    }

    /**
     * 带 PubMed 关键词的 B方案母稿生成。
     *
     * @param keywords PubMed 检索关键词列表，可为 null（由 AI 服务按人群默认映射）
     */
    public String generateArticleMotherDraftB(String topic, String persona, List<String> keywords) {
        log.info("开始生成文章母稿(B方案), topic={}, persona={}", topic, persona);
        if (circuitBreaker.isOpen()) {
            log.warn("AI服务熔断保护中，跳过文章母稿(B方案)生成");
            throw new RuntimeException(circuitBreaker.buildBreakerMessage());
        }
        try {
            Map<String, Object> requestBody = new LinkedHashMap<>();
            requestBody.put("topic", topic);
            requestBody.put("target_crowd", persona);
            if (keywords != null && !keywords.isEmpty()) {
                requestBody.put("keywords", keywords);
            }

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            // B方案含本地 Ollama 推理（Stage1 框架 + Stage3 校验），耗时较长，使用 300s 长超时模板
            ResponseEntity<String> response = restTemplateLong.postForEntity(
                    restClientConfig.getAiBaseUrl() + "/articles/mother-draft", entity, String.class);

            if (response.getBody() == null) {
                throw new RuntimeException("AI 服务返回空响应");
            }

            Map<String, Object> responseMap = objectMapper.readValue(response.getBody(), Map.class);
            // AI 服务统一响应结构：{success, code, message, data:{response,...}}，正文在 data.response
            String content = null;
            Object dataObj = responseMap.get("data");
            if (dataObj instanceof Map) {
                Object resp = ((Map<?, ?>) dataObj).get("response");
                content = resp != null ? String.valueOf(resp) : null;
            }
            if (content == null) {
                Object topResp = responseMap.get("response");
                if (topResp != null) {
                    content = String.valueOf(topResp);
                }
            }
            circuitBreaker.recordSuccess();
            log.info("文章母稿(B方案)生成完成, contentSize={}", content != null ? content.length() : 0);
            return content != null ? content : "";
        } catch (Exception e) {
            circuitBreaker.recordFailure();
            log.error("AI服务(B方案)调用失败: {}", e.getMessage(), e);
            throw new RuntimeException("调用 AI 生成母稿(B方案)失败: " + e.getMessage(), e);
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

            // 食谱生成走云端 Agent 编排，实测约 47s，必须用 300s 长超时模板，否则 30s 即超时并误触发熔断
            ResponseEntity<String> response = restTemplateLong.postForEntity(
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
     *
     * 架构收敛（RAG 职责归 AI 服务）：不再发送 Java 侧 system_prompt ——
     * AI 服务 /chat 不读取该字段，其内部 orchestrator 自行完成知识库检索与
     * 系统提示词组装（health_snapshot 已携带全部用户上下文）。
     */
    public String callAiService(Integer userId, String question, Map<String, Object> healthSnapshot) {
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

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            // 健康咨询为长调用（云端 DeepSeek 生成常超 30s），必须使用 300s 长超时模板
            ResponseEntity<String> response = restTemplateLong.postForEntity(
                    restClientConfig.getAiBaseUrl() + "/chat", entity, String.class);

            if (response.getBody() == null) {
                throw new RuntimeException("AI 服务返回空响应");
            }

            Map<String, Object> responseMap = objectMapper.readValue(response.getBody(), Map.class);
            // AI 服务统一响应结构：{success, code, message, data:{response,...}}，正文在 data.response
            String reply = (String) responseMap.get("response");
            if (reply == null) {
                Object dataObj = responseMap.get("data");
                if (dataObj instanceof Map) {
                    Object resp = ((Map<?, ?>) dataObj).get("response");
                    reply = resp != null ? String.valueOf(resp) : null;
                }
            }
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
