package com.health.controller;

import com.health.dto.AddMealRequest;
import com.health.dto.ApiResponse;
import com.health.entity.DietMeal;
import com.health.entity.User;
import com.health.service.DietService;
import com.health.service.FamilyRelationService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/diet")
public class DietController {

    private final DietService dietService;
    private final FamilyRelationService relationService;

    public DietController(DietService dietService, FamilyRelationService relationService) {
        this.dietService = dietService;
        this.relationService = relationService;
    }

    @PostMapping("/add")
    public ResponseEntity<ApiResponse<DietMeal>> addMeal(
            Authentication authentication,
            @RequestBody AddMealRequest request,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId) {
        User user = extractUser(authentication);
        if (user == null) return unauthorized();
        int operateAs = resolveOperateUserId(user.getUserId(), targetUserId);
        if (operateAs == -1) return forbidden("无权替该用户添加饮食记录");
        DietMeal meal = dietService.addMeal(operateAs, request);
        return ResponseEntity.ok(ApiResponse.success("饮食记录已添加", meal));
    }

    @DeleteMapping("/meal/{mealId}")
    public ResponseEntity<ApiResponse<Object>> deleteMeal(
            Authentication authentication,
            @PathVariable(name = "mealId") Integer mealId,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId) {
        User user = extractUser(authentication);
        if (user == null) return unauthorized();
        int operateAs = resolveOperateUserId(user.getUserId(), targetUserId);
        if (operateAs == -1) return forbidden("无权操作该用户的记录");
        boolean ok = dietService.deleteMeal(operateAs, mealId);
        if (!ok) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(ApiResponse.error(HttpStatus.NOT_FOUND.value(), "记录不存在或无权限"));
        }
        return ResponseEntity.ok(ApiResponse.success("已删除", null));
    }

    @GetMapping("/date/{date}")
    public ResponseEntity<ApiResponse<List<Map<String, Object>>>> getMealsByDate(
            Authentication authentication,
            @PathVariable(name = "date") String date,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId) {
        User user = extractUser(authentication);
        if (user == null) return unauthorized();
        int operateAs = resolveOperateUserId(user.getUserId(), targetUserId);
        if (operateAs == -1) return forbidden("无权查看该用户的饮食记录");
        List<Map<String, Object>> meals = dietService.getMealsByDate(operateAs, date);
        return ResponseEntity.ok(ApiResponse.success(meals));
    }

    @GetMapping("/analyze/{date}")
    public ResponseEntity<ApiResponse<Map<String, Object>>> analyzeDiet(
            Authentication authentication,
            @PathVariable(name = "date") String date,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId) {
        User user = extractUser(authentication);
        if (user == null) return unauthorized();
        int operateAs = resolveOperateUserId(user.getUserId(), targetUserId);
        if (operateAs == -1) return forbidden("无权查看该用户的营养分析");
        Map<String, Object> analysis = dietService.analyzeDiet(operateAs, date);
        return ResponseEntity.ok(ApiResponse.success(analysis));
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

    @SuppressWarnings("unchecked")
    private <T> ResponseEntity<ApiResponse<T>> unauthorized() {
        return (ResponseEntity<ApiResponse<T>>) (ResponseEntity)
                ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
    }

    @SuppressWarnings("unchecked")
    private <T> ResponseEntity<ApiResponse<T>> forbidden(String msg) {
        return (ResponseEntity<ApiResponse<T>>) (ResponseEntity)
                ResponseEntity.status(HttpStatus.FORBIDDEN).body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), msg));
    }
}
