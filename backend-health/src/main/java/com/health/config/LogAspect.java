package com.health.config;

import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;

import java.util.Arrays;

@Aspect
@Component
@Slf4j
public class LogAspect {

    @Around("execution(* com.health.controller..*.*(..))")
    public Object logController(ProceedingJoinPoint pjp) throws Throwable {
        String className = pjp.getTarget().getClass().getSimpleName();
        String methodName = pjp.getSignature().getName();
        Object[] args = pjp.getArgs();

        // 记录请求入口
        log.info("→ 进入 {}.{}() 请求参数: {}", className, methodName, Arrays.toString(args));

        long start = System.currentTimeMillis();
        Object result;
        try {
            result = pjp.proceed();
        } catch (Throwable e) {
            long elapsed = System.currentTimeMillis() - start;
            log.error("✗ {}.{}() 执行异常，耗时 {}ms，异常信息:", className, methodName, elapsed, e);
            throw e;
        }

        long elapsed = System.currentTimeMillis() - start;
        // 记录正常响应
        log.info("← {}.{}() 执行完成，耗时 {}ms，响应结果: {}", className, methodName, elapsed,
                result != null ? (result.toString().length() > 200 ? result.toString().substring(0, 200) + "..." : result.toString()) : "null");

        return result;
    }
}
