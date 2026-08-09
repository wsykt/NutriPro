package com.health.controller;

import com.health.dto.ApiResponse;
import com.health.entity.BodyMetricsHistory;
import com.health.entity.User;
import com.health.service.BodyMetricsHistoryService;
import com.health.service.FamilyRelationService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/metrics")
public class BodyMetricsHistoryController {

    private final BodyMetricsHistoryService metricsService;
    private final FamilyRelationService relationService;

    public BodyMetricsHistoryController(BodyMetricsHistoryService metricsService,
                                         FamilyRelationService relationService) {
        this.metricsService = metricsService;
        this.relationService = relationService;
    }

    @GetMapping("/history/{userId}")
    public ResponseEntity<ApiResponse<List<BodyMetricsHistory>>> getHistory(
            Authentication authentication,
            @PathVariable(name = "userId") Integer userId) {
        User user = extractUser(authentication);
        if (user == null) return unauthorized();
        if (!user.getUserId().equals(userId) && !relationService.isConfirmedGuardian(user.getUserId(), userId)) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(ApiResponse.error("无权查看该用户的数据"));
        }
        return ResponseEntity.ok(ApiResponse.success(metricsService.getHistory(userId)));
    }

    @GetMapping("/history/{userId}/range")
    public ResponseEntity<ApiResponse<List<BodyMetricsHistory>>> getHistoryByRange(
            Authentication authentication,
            @PathVariable(name = "userId") Integer userId,
            @RequestParam(name = "startDate") String startDate,
            @RequestParam(name = "endDate") String endDate) {
        User user = extractUser(authentication);
        if (user == null) return unauthorized();
        if (!user.getUserId().equals(userId) && !relationService.isConfirmedGuardian(user.getUserId(), userId)) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(ApiResponse.error("无权查看该用户的数据"));
        }
        return ResponseEntity.ok(ApiResponse.success(metricsService.getHistoryByRange(userId, startDate, endDate)));
    }

    /**
     * 健康时序预测：基于历史体重序列回归预测未来 days 天体重趋势。
     */
    @GetMapping("/predict/{userId}")
    public ResponseEntity<ApiResponse<java.util.Map<String, Object>>> predictWeightTrend(
            Authentication authentication,
            @PathVariable(name = "userId") Integer userId,
            @RequestParam(name = "days", defaultValue = "7") Integer days) {
        User user = extractUser(authentication);
        if (user == null) return unauthorized();
        if (!user.getUserId().equals(userId) && !relationService.isConfirmedGuardian(user.getUserId(), userId)) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(ApiResponse.error("无权查看该用户的数据"));
        }
        int d = (days == null || days < 1 || days > 30) ? 7 : days;
        return ResponseEntity.ok(ApiResponse.success(metricsService.predictWeightTrend(userId, d)));
    }

    /**
     * 手动保存一条历史身体指标（身高、体重、年龄、人群类型），用于补充旧数据或新建趋势点。
     * body 示例：{ "recordDate": "2026-06-20", "height": 172, "weight": 68, "age": 32, "crowdType": "普通人" }
     */
    @PostMapping("/save")
    public ResponseEntity<ApiResponse<BodyMetricsHistory>> saveMetrics(
            Authentication authentication,
            @RequestBody java.util.Map<String, Object> payload,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId) {
        User user = extractUser(authentication);
        if (user == null) return unauthorized();
        int operateAs = targetUserId == null || targetUserId.equals(user.getUserId())
                ? user.getUserId()
                : (relationService.isConfirmedGuardian(user.getUserId(), targetUserId) ? targetUserId : -1);
        if (operateAs == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(ApiResponse.error("无权操作该用户的数据"));
        }
        String recordDate = (String) payload.get("recordDate");
        if (recordDate == null || recordDate.trim().isEmpty()) {
            return ResponseEntity.badRequest().body(ApiResponse.error(HttpStatus.BAD_REQUEST.value(), "请提供日期"));
        }
        Double height = toDouble(payload.get("height"));
        Double weight = toDouble(payload.get("weight"));
        Integer age = toInteger(payload.get("age"));
        String crowdType = payload.get("crowdType") == null ? null : payload.get("crowdType").toString();
        BodyMetricsHistory history = metricsService.saveMetrics(operateAs, recordDate, height, weight, age, null, crowdType);
        return ResponseEntity.ok(ApiResponse.success("已保存历史指标", history));
    }

    @DeleteMapping("/delete")
    public ResponseEntity<ApiResponse<Boolean>> deleteMetrics(
            Authentication authentication,
            @RequestParam(name = "recordDate") String recordDate,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId) {
        User user = extractUser(authentication);
        if (user == null) return unauthorized();
        int operateAs = targetUserId == null || targetUserId.equals(user.getUserId())
                ? user.getUserId()
                : (relationService.isConfirmedGuardian(user.getUserId(), targetUserId) ? targetUserId : -1);
        if (operateAs == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(ApiResponse.error("无权操作该用户的数据"));
        }
        boolean deleted = metricsService.deleteByDate(operateAs, recordDate);
        return ResponseEntity.ok(ApiResponse.success(deleted ? "已删除" : "该日期无记录", deleted));
    }

    private Double toDouble(Object value) {
        if (value == null) return null;
        if (value instanceof Number) return ((Number) value).doubleValue();
        try {
            return Double.parseDouble(value.toString().trim());
        } catch (Exception ignored) {
            return null;
        }
    }

    private Integer toInteger(Object value) {
        if (value == null) return null;
        if (value instanceof Number) return ((Number) value).intValue();
        try {
            return Integer.parseInt(value.toString().trim());
        } catch (Exception ignored) {
            return null;
        }
    }

    private User extractUser(Authentication authentication) {
        if (authentication == null || authentication.getPrincipal() == null) return null;
        Object principal = authentication.getPrincipal();
        if (principal instanceof User) return (User) principal;
        return null;
    }

    @SuppressWarnings("unchecked")
    private <T> ResponseEntity<ApiResponse<T>> unauthorized() {
        return (ResponseEntity<ApiResponse<T>>) (ResponseEntity)
                ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(ApiResponse.error("请先登录"));
    }
}
