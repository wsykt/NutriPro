package com.health.util;

import org.springframework.stereotype.Component;

import java.util.concurrent.atomic.AtomicInteger;

/**
 * 线程安全的 AI 服务熔断器。
 *
 * 状态机：
 * - CLOSED：正常，连续失败达到阈值后进入 OPEN
 * - OPEN：冷却窗口内快速失败；冷却期结束后进入 HALF_OPEN 允许一次试探请求
 * - HALF_OPEN：试探请求成功回到 CLOSED，失败则重新打开
 *
 * 计数使用 AtomicInteger、状态使用 volatile，保证多线程并发访问下的安全性。
 *
 * 作为 Spring 单例 Bean 注入到各 AI 业务服务，保证整个后端共享同一熔断状态
 * （任一服务连续失败达到阈值，其余服务同步熔断，避免继续打爆 AI 服务）。
 */
@Component
public class CircuitBreaker {

    public enum State { CLOSED, OPEN, HALF_OPEN }

    /** 默认熔断阈值：连续失败 3 次 */
    private static final int DEFAULT_THRESHOLD = 3;
    /** 默认冷却时间：60 秒 */
    private static final long DEFAULT_RESET_MS = 60000;

    private final int threshold;
    private final long resetMs;

    /** 连续失败次数（原子计数器，线程安全） */
    private final AtomicInteger consecutiveFailures = new AtomicInteger(0);

    /** 当前状态（volatile，保证多线程可见性） */
    private volatile State state = State.CLOSED;

    /** 熔断打开的时间戳（毫秒） */
    private volatile long openedAt = 0;

    public CircuitBreaker() {
        this(DEFAULT_THRESHOLD, DEFAULT_RESET_MS);
    }

    public CircuitBreaker(int threshold, long resetMs) {
        this.threshold = threshold;
        this.resetMs = resetMs;
    }

    /**
     * 判断当前是否处于熔断状态（需要快速失败）。
     * 处于 OPEN 且冷却期已过时，转为 HALF_OPEN 放行一次试探请求。
     */
    public boolean isOpen() {
        if (state == State.OPEN) {
            if (System.currentTimeMillis() >= openedAt + resetMs) {
                state = State.HALF_OPEN; // 冷却结束，半开试探
            } else {
                return true;
            }
        }
        return false;
    }

    /** 记录一次成功调用：重置计数并恢复 CLOSED */
    public void recordSuccess() {
        consecutiveFailures.set(0);
        state = State.CLOSED;
        openedAt = 0;
    }

    /** 记录一次失败调用：累计连续失败，达到阈值则打开熔断；半开状态失败则立即重新打开 */
    public void recordFailure() {
        if (state == State.HALF_OPEN) {
            state = State.OPEN;
            openedAt = System.currentTimeMillis();
            return;
        }
        if (consecutiveFailures.incrementAndGet() >= threshold) {
            state = State.OPEN;
            openedAt = System.currentTimeMillis();
        }
    }

    /** 当前状态 */
    public State getState() {
        return state;
    }

    /** 连续失败次数 */
    public int getConsecutiveFailures() {
        return consecutiveFailures.get();
    }

    /** 剩余冷却毫秒数（未处于熔断打开状态时为 0） */
    public long getRemainingCooldownMs() {
        if (state != State.OPEN) return 0;
        long remaining = openedAt + resetMs - System.currentTimeMillis();
        return remaining > 0 ? remaining : 0;
    }

    /** 生成熔断保护提示文案（各 AI 业务服务统一复用） */
    public String buildBreakerMessage() {
        return "⚠️ AI 服务暂时熔断保护中（连续失败 " + getConsecutiveFailures() + " 次），"
                + "请等待 " + (getRemainingCooldownMs() / 1000) + " 秒后重试。";
    }
}
