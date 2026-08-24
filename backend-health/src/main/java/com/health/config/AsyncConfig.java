package com.health.config;

import org.slf4j.MDC;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.task.TaskDecorator;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.Map;
import java.util.concurrent.ThreadPoolExecutor;

/**
 * 后端异步化线程池配置（阶段一·举措1）。
 *
 * 用途：AI 长任务（科普文章生成/混合架构生成/自纠错重新生成）提交到独立线程池执行，
 * 避免阻塞 HTTP 请求线程，前端可通过任务状态接口轮询进度。
 *
 * 关键设计：
 * 1. 核心 2 / 最大 8 / 队列 20：单机竞赛场景足够，避免线程过度扩张
 * 2. CallerRunsPolicy 拒绝策略：满载时由调用线程执行，保证任务不丢失（同步兜底）
 * 3. TaskDecorator 透传 MDC：异步线程继承主线程的 traceId / userId，保证全链路日志可串联
 */
@Configuration
@EnableAsync
public class AsyncConfig {

    /** AI 长任务线程池 */
    @Bean(name = "aiTaskExecutor")
    public ThreadPoolTaskExecutor aiTaskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(2);
        executor.setMaxPoolSize(8);
        executor.setQueueCapacity(20);
        executor.setThreadNamePrefix("ai-task-");
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(30);
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        // TraceId / userId 全链路透传：异步线程继承调用线程的 MDC 上下文
        executor.setTaskDecorator(mdcPropagateDecorator());
        executor.initialize();
        return executor;
    }

    /**
     * MDC 上下文透传装饰器：提交任务时快照主线程 MDC，
     * 执行时恢复到工作线程，执行完清理，避免上下文串扰。
     */
    private TaskDecorator mdcPropagateDecorator() {
        return runnable -> {
            Map<String, String> contextMap = MDC.getCopyOfContextMap();
            return () -> {
                try {
                    if (contextMap != null && !contextMap.isEmpty()) {
                        MDC.setContextMap(contextMap);
                    }
                    runnable.run();
                } finally {
                    MDC.clear();
                }
            };
        };
    }
}
