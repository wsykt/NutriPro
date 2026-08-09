package com.health.controller;

import com.health.dto.ApiResponse;
import com.health.entity.FamilyRelation;
import com.health.entity.User;
import com.health.service.FamilyRelationService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/relation")
public class FamilyRelationController {

    private final FamilyRelationService relationService;

    public FamilyRelationController(FamilyRelationService relationService) {
        this.relationService = relationService;
    }

    @PostMapping("/add")
    public ResponseEntity<ApiResponse<FamilyRelation>> addRelation(
            Authentication authentication,
            @RequestBody Map<String, String> request) {
        User user = extractUser(authentication);
        if (user == null) return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(ApiResponse.error("请先登录"));
        try {
            FamilyRelation r = relationService.addRelation(user.getUserId(), request.get("wardUsername"));
            return ResponseEntity.ok(ApiResponse.success("邀请已发出，等待对方确认", r));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }

    @PostMapping("/confirm/{relationId}")
    public ResponseEntity<ApiResponse<FamilyRelation>> confirmRelation(
            Authentication authentication,
            @PathVariable(name = "relationId") Integer relationId) {
        User user = extractUser(authentication);
        if (user == null) return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(ApiResponse.error("请先登录"));
        try {
            FamilyRelation r = relationService.confirmRelation(user.getUserId(), relationId);
            return ResponseEntity.ok(ApiResponse.success("已确认亲属关系", r));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }

    @PostMapping("/reject/{relationId}")
    public ResponseEntity<ApiResponse<FamilyRelation>> rejectRelation(
            Authentication authentication,
            @PathVariable(name = "relationId") Integer relationId) {
        User user = extractUser(authentication);
        if (user == null) return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(ApiResponse.error("请先登录"));
        try {
            FamilyRelation r = relationService.rejectRelation(user.getUserId(), relationId);
            return ResponseEntity.ok(ApiResponse.success("已拒绝", r));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }

    @GetMapping("/my-wards")
    public ResponseEntity<ApiResponse<List<FamilyRelation>>> getMyWards(Authentication authentication) {
        User user = extractUser(authentication);
        if (user == null) return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(ApiResponse.error("请先登录"));
        return ResponseEntity.ok(ApiResponse.success(relationService.getMyWards(user.getUserId())));
    }

    @GetMapping("/my-guardians")
    public ResponseEntity<ApiResponse<List<FamilyRelation>>> getMyGuardians(Authentication authentication) {
        User user = extractUser(authentication);
        if (user == null) return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(ApiResponse.error("请先登录"));
        return ResponseEntity.ok(ApiResponse.success(relationService.getMyGuardians(user.getUserId())));
    }

    @GetMapping("/pending-invitations")
    public ResponseEntity<ApiResponse<List<FamilyRelation>>> getPendingInvitations(Authentication authentication) {
        User user = extractUser(authentication);
        if (user == null) return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(ApiResponse.error("请先登录"));
        return ResponseEntity.ok(ApiResponse.success(relationService.getPendingInvitations(user.getUserId())));
    }

    @DeleteMapping("/{relationId}")
    public ResponseEntity<ApiResponse<Void>> deleteRelation(
            Authentication authentication,
            @PathVariable(name = "relationId") Integer relationId) {
        User user = extractUser(authentication);
        if (user == null) return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(ApiResponse.error("请先登录"));
        try {
            relationService.deleteRelation(user.getUserId(), relationId);
            return ResponseEntity.ok(ApiResponse.success("关系已删除", null));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }

    private User extractUser(Authentication authentication) {
        if (authentication == null || authentication.getPrincipal() == null) return null;
        Object principal = authentication.getPrincipal();
        if (principal instanceof User) return (User) principal;
        return null;
    }
}
