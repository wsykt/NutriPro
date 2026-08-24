package com.health.util;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * 固定窗口限流器（内存版，零外部依赖）。
 *
 * 线程安全：每个 key 独立计数窗口，窗口过期自动重置。
 * 适用于单实例部署；多实例/集群场景应换成 Redis 等集中式限流。
 */
public class RateLimiter {

    /** 窗口内最大请求数 */
    private final int maxRequests;
    /** 窗口时长（毫秒） */
    private final long windowMillis;
    /** key -> 窗口计数 */
    private final ConcurrentHashMap<String, WindowCounter> buckets = new ConcurrentHashMap<>();

    public RateLimiter(int maxRequests, long windowMillis) {
        if (maxRequests <= 0 || windowMillis <= 0) {
            throw new IllegalArgumentException("maxRequests 与 windowMillis 必须为正数");
        }
        this.maxRequests = maxRequests;
        this.windowMillis = windowMillis;
    }

    /**
     * 尝试获取一次配额。
     *
     * @param key 限流维度（如客户端 IP、用户 ID）
     * @return true=允许通过；false=已超限（应返回 429）
     */
    public boolean tryAcquire(String key) {
        if (key == null || key.isEmpty()) {
            key = "anonymous";
        }
        final String finalKey = key;
        long now = System.currentTimeMillis();
        WindowCounter counter = buckets.compute(finalKey, (k, existing) -> {
            if (existing == null || now - existing.windowStart >= windowMillis) {
                // 新窗口（顺带清理过期数据）
                return new WindowCounter(now);
            }
            return existing;
        });
        // 周期清理过期 key，防止内存无限增长（配合伪造 key 的 DoS 场景）
        cleanupExpired();
        return counter.count.incrementAndGet() <= maxRequests;
    }

    /** 惰性清理：过期窗口的 key 直接移除（每次调用最多扫描一次全表，成本可控） */
    private void cleanupExpired() {
        if ((cleanupTick.incrementAndGet() & 63) != 0) return; // 每 64 次调用清理一次
        long now = System.currentTimeMillis();
        buckets.entrySet().removeIf(e -> now - e.getValue().windowStart >= windowMillis);
    }

    private final java.util.concurrent.atomic.AtomicLong cleanupTick = new java.util.concurrent.atomic.AtomicLong(0);

    /** 清理全部窗口（一般仅在测试或重置场景使用） */
    public void reset() {
        buckets.clear();
    }

    /** 当前活跃 key 数量（调试/监控用） */
    public int size() {
        return buckets.size();
    }

    private static final class WindowCounter {
        final long windowStart;
        final AtomicInteger count = new AtomicInteger(0);

        WindowCounter(long windowStart) {
            this.windowStart = windowStart;
        }
    }
}
