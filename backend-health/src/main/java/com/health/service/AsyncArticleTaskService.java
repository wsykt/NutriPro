package com.health.service;

import com.health.config.TraceIdFilter;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.MDC;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * AI 长任务异步化服务（阶段一·举措1）。
 *
 * 将耗时的 AI 任务（科普文章生成 / 混合架构生成 / 自纠错重新生成）提交到独立线程池执行，
 * 接口立即返回 taskId，前端轮询 {@link #getTaskStatus(String)} 获取进度与结果。
 * 同步接口（ArticleController 原有 /generate 等）保留作为兜底，互不影响。
 *
 * 任务状态机：PENDING → RUNNING → SUCCESS / FAILED
 */
@Slf4j
@Service
public class AsyncArticleTaskService {

    /** 内存任务注册表：taskId -> 任务快照（含状态、进度、结果/错误） */
    private final Map<String, Map<String, Object>> taskStore = new ConcurrentHashMap<>();

    /** 已完成任务最大保留条数，防止内存无限增长 */
    private static final int MAX_RETAINED_TASKS = 200;

    @Autowired
    @Lazy
    private AsyncArticleTaskService self;

    @Autowired
    private ArticleService articleService;

    // ======================== 任务提交（HTTP 线程立即返回 taskId） ========================

    /** 提交 RAG 模式文章生成任务 */
    public String submitArticleGeneration(String topic, String persona) {
        return submit(topic, persona, "rag", -1);
    }

    /** 提交混合架构（方案C）文章生成任务 */
    public String submitHybridGeneration(String topic, String persona) {
        return submit(topic, persona, "hybrid", -1);
    }

    /** 提交自纠错重新生成任务 */
    public String submitRegenerate(Integer articleId) {
        return submit(null, null, "regenerate", articleId);
    }

    /** 统一提交：登记 PENDING 任务并触发异步执行 */
    private String submit(String topic, String persona, String type, Integer articleId) {
        String taskId = "task-" + UUID.randomUUID().toString().replace("-", "").substring(0, 12);
        Map<String, Object> task = new ConcurrentHashMap<>();
        task.put("taskId", taskId);
        task.put("type", type);
        task.put("status", "PENDING");
        task.put("topic", topic);
        task.put("persona", persona);
        task.put("articleId", articleId);
        task.put("traceId", MDC.get(TraceIdFilter.TRACE_ID_MDC));
        task.put("submitTime", System.currentTimeMillis());
        task.put("message", "任务已提交，等待线程池调度");
        taskStore.put(taskId, task);
        log.info("异步任务已提交, taskId={}, type={}, topic={}", taskId, type, topic);

        // 通过 self 代理调用 @Async 方法，保证异步注解生效（避免自调用绕过代理）
        if ("hybrid".equals(type)) {
            self.runHybridGenerationAsync(taskId, topic, persona);
        } else if ("regenerate".equals(type)) {
            self.runRegenerateAsync(taskId, articleId);
        } else {
            self.runArticleGenerationAsync(taskId, topic, persona);
        }
        return taskId;
    }

    // ======================== 异步执行（aiTaskExecutor 线程池） ========================

    /** RAG 模式文章生成 */
    @Async("aiTaskExecutor")
    public void runArticleGenerationAsync(String taskId, String topic, String persona) {
        log.info("异步任务开始执行: taskId={}, mode=rag, topic={}", taskId, topic);
        updateStatus(taskId, "RUNNING", "正在检索知识库并生成文章母稿...");
        try {
            Map<String, Object> result = articleService.generateAndSave(topic, persona);
            complete(taskId, result, "文章生成完成");
        } catch (Exception e) {
            fail(taskId, e);
        }
    }

    /** 混合架构（方案C）文章生成 */
    @Async("aiTaskExecutor")
    public void runHybridGenerationAsync(String taskId, String topic, String persona) {
        log.info("异步任务开始执行: taskId={}, mode=hybrid, topic={}", taskId, topic);
        updateStatus(taskId, "RUNNING", "正在混合架构生成（RAG 检索 + Agent 联网 + 事实校验）...");
        try {
            Map<String, Object> result = articleService.generateAndSaveHybrid(topic, persona);
            complete(taskId, result, "混合架构文章生成完成");
        } catch (Exception e) {
            fail(taskId, e);
        }
    }

    /** 自纠错重新生成 */
    @Async("aiTaskExecutor")
    public void runRegenerateAsync(String taskId, Integer articleId) {
        log.info("异步任务开始执行: taskId={}, mode=regenerate, articleId={}", taskId, articleId);
        updateStatus(taskId, "RUNNING", "正在重新生成文章（注入历史质量纠错反馈）...");
        try {
            Map<String, Object> result = articleService.regenerateWithCorrection(articleId);
            complete(taskId, result, "自纠错重新生成完成");
        } catch (Exception e) {
            fail(taskId, e);
        }
    }

    // ======================== 任务状态查询 ========================

    /**
     * 查询任务状态。返回任务快照副本，避免外部修改内部状态。
     */
    public Map<String, Object> getTaskStatus(String taskId) {
        Map<String, Object> task = taskStore.get(taskId);
        if (task == null) {
            Map<String, Object> notFound = new LinkedHashMap<>();
            notFound.put("code", 404);
            notFound.put("message", "任务不存在或已过期清理");
            return notFound;
        }
        Map<String, Object> snapshot = new LinkedHashMap<>();
        snapshot.put("code", 200);
        snapshot.put("taskId", task.get("taskId"));
        snapshot.put("type", task.get("type"));
        snapshot.put("status", task.get("status"));
        snapshot.put("topic", task.get("topic"));
        snapshot.put("persona", task.get("persona"));
        snapshot.put("articleId", task.get("articleId"));
        snapshot.put("traceId", task.get("traceId"));
        snapshot.put("message", task.get("message"));
        snapshot.put("submitTime", task.get("submitTime"));
        snapshot.put("finishTime", task.get("finishTime"));
        snapshot.put("elapsedMs", task.get("elapsedMs"));
        if (task.get("result") != null) {
            snapshot.put("result", task.get("result"));
        }
        if (task.get("error") != null) {
            snapshot.put("error", task.get("error"));
        }
        return snapshot;
    }

    // ======================== 内部状态管理 ========================

    private void updateStatus(String taskId, String status, String message) {
        Map<String, Object> task = taskStore.get(taskId);
        if (task != null) {
            task.put("status", status);
            task.put("message", message);
        }
    }

    private void complete(String taskId, Map<String, Object> result, String message) {
        Map<String, Object> task = taskStore.get(taskId);
        if (task != null) {
            task.put("status", "SUCCESS");
            task.put("message", message);
            task.put("result", result);
            task.put("finishTime", System.currentTimeMillis());
            task.put("elapsedMs", System.currentTimeMillis() - (Long) task.get("submitTime"));
        }
        log.info("异步任务完成: taskId={}, status=SUCCESS, elapsedMs={}",
                taskId, task != null ? task.get("elapsedMs") : -1);
        trimTaskStore();
    }

    private void fail(String taskId, Exception e) {
        Map<String, Object> task = taskStore.get(taskId);
        if (task != null) {
            task.put("status", "FAILED");
            task.put("message", "任务执行失败");
            task.put("error", e.getMessage());
            task.put("finishTime", System.currentTimeMillis());
            task.put("elapsedMs", System.currentTimeMillis() - (Long) task.get("submitTime"));
        }
        log.error("异步任务失败: taskId={}, error={}", taskId, e.getMessage(), e);
    }

    /** 容量控制：仅清理已完成（SUCCESS/FAILED）的旧任务，运行中任务不受影响 */
    private void trimTaskStore() {
        if (taskStore.size() <= MAX_RETAINED_TASKS) {
            return;
        }
        int overflow = taskStore.size() - MAX_RETAINED_TASKS;
        int removed = 0;
        Iterator<Map.Entry<String, Map<String, Object>>> it = taskStore.entrySet().iterator();
        while (it.hasNext() && removed < overflow) {
            Map<String, Object> task = it.next().getValue();
            String status = String.valueOf(task.get("status"));
            if ("SUCCESS".equals(status) || "FAILED".equals(status)) {
                it.remove();
                removed++;
            }
        }
    }
}
