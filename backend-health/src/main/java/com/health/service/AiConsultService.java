package com.health.service;

import com.health.config.RestClientConfig;
import com.health.entity.*;
import com.health.repository.*;
import com.health.util.CircuitBreaker;
import com.health.util.RagVectorSearchUtil;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import javax.annotation.PostConstruct;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.*;

/**
 * AI 健康咨询域：同步咨询 / 流式咨询。
 *
 * 从原 AiChatService 拆分出的「咨询域」：
 * - consult：完整链路（健康快照 + RAG 检索 + 系统提示词 + AI 调用 + 记录落库）
 * - consultStream：SSE 流式转发（HttpURLConnection 逐行透传 AI 服务事件）
 *
 * 注意：consult 方法【不】持有事务 —— 只读查询、RAG 检索与最长 30s 的 AI HTTP 调用
 * 均在无事务状态下执行（避免 SQLite 单写者下长事务阻塞所有写操作），仅在最后通过
 * recordRepository.save() 以独立短事务落库。
 */
@Slf4j
@Service
public class AiConsultService {

    private final CircuitBreaker circuitBreaker;
    private final UserRepository userRepository;
    private final AiConversationRecordRepository recordRepository;
    private final AiChatContextBuilder contextBuilder;
    private final AiChatClientService aiChatClient;
    private final RagVectorSearchUtil ragSearchUtil;

    @Autowired
    @Qualifier("aiRestTemplate")
    private RestTemplate restTemplate;

    /** AI 长任务受管线程池（core 2 / max 8，用于 SSE 流式转发，替代原始 new Thread） */
    @Autowired
    @Qualifier("aiTaskExecutor")
    private ThreadPoolTaskExecutor aiTaskExecutor;

    /** 固定尾部温馨提示（后端拼接，不由 AI 生成） */
    private static final String FIXED_DISCLAIMER =
            "\n\n温馨提示：以上仅为营养参考方案，存在基础疾病请遵医嘱。";

    public AiConsultService(CircuitBreaker circuitBreaker,
                            UserRepository userRepository,
                            AiConversationRecordRepository recordRepository,
                            AiChatContextBuilder contextBuilder,
                            AiChatClientService aiChatClient) {
        this.circuitBreaker = circuitBreaker;
        this.userRepository = userRepository;
        this.recordRepository = recordRepository;
        this.contextBuilder = contextBuilder;
        this.aiChatClient = aiChatClient;
        // BGE 向量检索工具（非 Spring Bean，直接实例化）
        this.ragSearchUtil = new RagVectorSearchUtil();
    }

    @PostConstruct
    public void init() {
        this.ragSearchUtil.setRestTemplate(restTemplate);
        this.ragSearchUtil.setAiBaseUrl(aiChatClient.getRestClientConfig().getAiBaseUrl());
    }

    /**
     * AI 健康咨询（同步完整链路）。
     */
    public Map<String, Object> consult(Integer userId, String question) {
        log.info("开始AI健康咨询, userId={}, question={}", userId,
                question != null && question.length() > 50 ? question.substring(0, 50) + "..." : question);
        User user = userRepository.findById(userId).orElse(null);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }

        String today = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);

        // 1. 构建健康数据快照（含身体数据 + 运动数据 + 饮食数据）
        Map<String, Object> snapshot = contextBuilder.buildHealthSnapshot(user, today);
        String snapshotJson;
        try {
            snapshotJson = aiChatClient.getObjectMapper().writeValueAsString(snapshot);
        } catch (Exception e) {
            snapshotJson = "{}";
        }

        // 2. RAG 向量检索：知识性问题触发检索，日常分析/计划不强制检索
        String ragKnowledge = "";
        if (RagVectorSearchUtil.shouldRetrieveForConsultation(question)) {
            String crowdType = user.getCrowdType() != null ? user.getCrowdType() : "";
            ragKnowledge = ragSearchUtil.search(question, 3, crowdType);
        }

        // 3. 构建系统提示词（v2.1：分层架构 + 后端前置计算 + RAG 知识注入）
        String systemPrompt = contextBuilder.buildSystemPrompt(user, snapshot, ragKnowledge);

        // 4. 调用 AI 服务（携带系统提示词）
        String reply = aiChatClient.callAiService(userId, question, snapshot, systemPrompt);

        // 5. 后端拼接固定尾部温馨提示（不由 AI 生成）
        reply = reply + FIXED_DISCLAIMER;

        // 6. 保存记录
        AiConversationRecord record = new AiConversationRecord();
        record.setUserId(userId);
        record.setModel("AI_SERVICE");
        record.setQuestion(question);
        record.setReply(reply);
        record.setHealthSnapshotJson(snapshotJson);
        record = recordRepository.save(record);

        // 7. 返回结果
        Map<String, Object> result = new HashMap<>();
        result.put("recordId", record.getId());
        result.put("reply", reply);
        result.put("forUserId", userId);
        result.put("forUsername", user.getUsername());
        result.put("snapshot", snapshot);
        result.put("ragUsed", !ragKnowledge.isEmpty());
        return result;
    }

    /**
     * 流式 AI 咨询：构建健康快照后转发 AI 服务的 /chat/stream SSE 流。
     * 因 RestTemplate 不支持 SSE 流式响应，这里使用 HttpURLConnection 逐行读取并
     * 转发到 Spring SseEmitter（事件类型透传：thinking/delta/done/error）。
     * 使用受管线程池 aiTaskExecutor 执行，避免每次请求原始 new Thread 创建线程。
     * @param highPerformance 高性能模式开关（true=AI 服务走真流式云端生成，false=完整链路）
     */
    public void consultStream(SseEmitter emitter, Integer userId, String question, boolean highPerformance) {
        aiTaskExecutor.execute(() -> {
            HttpURLConnection conn = null;
            try {
                if (circuitBreaker.isOpen()) {
                    log.warn("AI服务熔断保护中，跳过流式咨询");
                    emitter.send(SseEmitter.event().name("error")
                            .data("{\"message\":\"" + aiChatClient.escapeJson(circuitBreaker.buildBreakerMessage()) + "\"}"));
                    emitter.complete();
                    return;
                }
                User user = userRepository.findById(userId).orElse(null);
                if (user == null) {
                    emitter.send(SseEmitter.event().name("error").data("{\"message\":\"用户不存在\"}"));
                    emitter.complete();
                    return;
                }
                String today = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);
                Map<String, Object> snapshot = contextBuilder.buildHealthSnapshot(user, today);

                // 构造 AI 服务请求体（与 /consult 保持一致，透传 health_snapshot）
                Map<String, Object> requestBody = new LinkedHashMap<>();
                requestBody.put("message", question);
                requestBody.put("user_id", userId);
                requestBody.put("health_snapshot", snapshot);
                requestBody.put("high_performance", highPerformance);

                URL url = new URL(aiChatClient.getRestClientConfig().getAiBaseUrl() + "/chat/stream");
                conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setDoOutput(true);
                conn.setConnectTimeout(5000);
                conn.setReadTimeout(60000);
                conn.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                conn.setRequestProperty("Accept", "text/event-stream");

                try (OutputStream os = conn.getOutputStream()) {
                    os.write(aiChatClient.getObjectMapper().writeValueAsBytes(requestBody));
                    os.flush();
                }

                int code = conn.getResponseCode();
                if (code != 200) {
                    circuitBreaker.recordFailure();
                    String errBody = "";
                    if (conn.getErrorStream() != null) {
                        errBody = new String(aiChatClient.readAll(conn.getErrorStream()), StandardCharsets.UTF_8);
                    }
                    emitter.send(SseEmitter.event().name("error")
                            .data("{\"message\":\"AI 服务返回异常(" + code + "): " + aiChatClient.escapeJson(errBody) + "\"}"));
                    emitter.complete();
                    return;
                }

                // 逐行读取 SSE 事件并转发（event: xxx / data: {json}）
                try (BufferedReader reader = new BufferedReader(
                        new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8))) {
                    String eventType = null;
                    StringBuilder dataBuf = new StringBuilder();
                    String line;
                    while ((line = reader.readLine()) != null) {
                        if (line.isEmpty()) {
                            // 事件结束，转发
                            if (eventType != null && dataBuf.length() > 0) {
                                emitter.send(SseEmitter.event().name(eventType).data(dataBuf.toString()));
                            }
                            eventType = null;
                            dataBuf = new StringBuilder();
                            continue;
                        }
                        if (line.startsWith("event:")) {
                            eventType = line.substring(6).trim();
                        } else if (line.startsWith("data:")) {
                            dataBuf.append(line.substring(5).trim());
                        }
                    }
                    // 兜底：最后一条未以空行结束的事件
                    if (eventType != null && dataBuf.length() > 0) {
                        emitter.send(SseEmitter.event().name(eventType).data(dataBuf.toString()));
                    }
                }
                circuitBreaker.recordSuccess();
                emitter.complete();
            } catch (Exception e) {
                circuitBreaker.recordFailure();
                log.error("SSE 流式咨询转发失败: {}", e.getMessage(), e);
                try {
                    emitter.send(SseEmitter.event().name("error")
                            .data("{\"message\":\"流式咨询失败: " + aiChatClient.escapeJson(String.valueOf(e.getMessage())) + "\"}"));
                } catch (Exception ignore) {
                    // emitter 已断开，忽略
                }
                emitter.complete();
            } finally {
                if (conn != null) conn.disconnect();
            }
        });
    }
}
