package com.health.controller;

import com.health.dto.ApiResponse;
import com.health.dto.RegisterRequest;
import com.health.entity.BodyMetricsHistory;
import com.health.entity.User;
import com.health.service.BodyMetricsHistoryService;
import com.health.service.FamilyRelationService;
import com.health.service.ProfileService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.Map;

@RestController
@RequestMapping("/api/profile")
public class ProfileController {

    private final ProfileService profileService;
    private final FamilyRelationService relationService;
    private final BodyMetricsHistoryService metricsService;

    public ProfileController(ProfileService profileService,
                             FamilyRelationService relationService,
                             BodyMetricsHistoryService metricsService) {
        this.profileService = profileService;
        this.relationService = relationService;
        this.metricsService = metricsService;
    }

    @GetMapping("/info")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getProfile(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId) {
        User user = extractUser(authentication);
        if (user == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }
        int operateAs = resolveOperateUserId(user.getUserId(), targetUserId);
        if (operateAs == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权操作该用户，请先确认亲属关系"));
        }
        Map<String, Object> info = profileService.getUserInfo(operateAs);
        if (info == null) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(ApiResponse.error(HttpStatus.BAD_REQUEST.value(), "用户不存在"));
        }
        info.put("operateAsUserId", operateAs);
        return ResponseEntity.ok(ApiResponse.success(info));
    }

    @PutMapping("/update")
    public ResponseEntity<ApiResponse<Map<String, Object>>> updateProfile(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId,
            @RequestBody RegisterRequest request) {
        User user = extractUser(authentication);
        if (user == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }
        int operateAs = resolveOperateUserId(user.getUserId(), targetUserId);
        if (operateAs == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权操作该用户，请先确认亲属关系"));
        }
        Map<String, Object> result = profileService.updateProfileWithSnapshot(operateAs, request);
        return ResponseEntity.ok(ApiResponse.success("已保存资料，并写入今日身体指标快照", result));
    }

    @PutMapping("/dietary")
    public ResponseEntity<ApiResponse<User>> updateDietaryProfile(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId,
            @RequestBody Map<String, Object> dietaryProfile) {
        User user = extractUser(authentication);
        if (user == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }
        int operateAs = resolveOperateUserId(user.getUserId(), targetUserId);
        if (operateAs == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权操作该用户"));
        }
        User updated = profileService.updateDietaryProfile(operateAs, dietaryProfile);
        return ResponseEntity.ok(ApiResponse.success("饮食档案已更新", updated));
    }

    /**
     * 手动快照：把当前用户资料保存为一条 body_metrics_history 记录。
     * 即使资料没有变化，也允许用户主动保存，用于建立趋势线的初始点。
     */
    @PostMapping("/snapshot")
    public ResponseEntity<ApiResponse<BodyMetricsHistory>> snapshot(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId,
            @RequestParam(name = "date", required = false) String date) {
        User user = extractUser(authentication);
        if (user == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }
        int operateAs = resolveOperateUserId(user.getUserId(), targetUserId);
        if (operateAs == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权操作该用户"));
        }
        LocalDate localDate = (date != null && !date.trim().isEmpty()) ? LocalDate.parse(date) : LocalDate.now();
        BodyMetricsHistory snapshot = metricsService.snapshotFromUser(operateAs, localDate);
        return ResponseEntity.ok(ApiResponse.success("已保存快照", snapshot));
    }

    private int resolveOperateUserId(Integer currentUserId, Integer targetUserId) {
        if (targetUserId == null || targetUserId.equals(currentUserId)) return currentUserId;
        if (relationService.isConfirmedGuardian(currentUserId, targetUserId)) return targetUserId;
        return -1;
    }

    private User extractUser(Authentication authentication) {
        if (authentication == null || authentication.getPrincipal() == null) return null;
        Object principal = authentication.getPrincipal();
        if (principal instanceof User) return (User) principal;
        return null;
    }
}
