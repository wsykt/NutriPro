package com.health.controller;

import com.health.dto.ApiResponse;
import com.health.entity.NutritionReport;
import com.health.entity.User;
import com.health.service.BodyMetricsHistoryService;
import com.health.service.FamilyRelationService;
import com.health.service.NutritionReportService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/report")
public class NutritionReportController {

    private final NutritionReportService reportService;
    private final FamilyRelationService relationService;
    private final BodyMetricsHistoryService metricsService;

    public NutritionReportController(NutritionReportService reportService,
                                      FamilyRelationService relationService,
                                      BodyMetricsHistoryService metricsService) {
        this.reportService = reportService;
        this.relationService = relationService;
        this.metricsService = metricsService;
    }

    @PostMapping("/save")
    public ResponseEntity<ApiResponse<NutritionReport>> saveReport(
            Authentication authentication,
            @RequestBody Map<String, Object> request,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId) {
        User user = extractUser(authentication);
        if (user == null) return unauthorized();
        int operateAs = resolveOperateUserId(user.getUserId(), targetUserId);
        if (operateAs == -1) return forbidden("无权替该用户保存报告");
        NutritionReport report = reportService.saveReport(operateAs, request);
        try {
            metricsService.snapshotFromUser(operateAs, report.getReportDate());
        } catch (Exception ignore) {
        }
        return ResponseEntity.ok(ApiResponse.success("报告已保存", report));
    }

    @GetMapping("/date/{date}")
    public ResponseEntity<ApiResponse<NutritionReport>> getReportByDate(
            Authentication authentication,
            @PathVariable(name = "date") String date,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId) {
        User user = extractUser(authentication);
        if (user == null) return unauthorized();
        int operateAs = resolveOperateUserId(user.getUserId(), targetUserId);
        if (operateAs == -1) return forbidden("无权查看该用户的报告");
        NutritionReport report = reportService.getReportByDate(operateAs, LocalDate.parse(date))
                .orElse(null);
        return ResponseEntity.ok(ApiResponse.success(report));
    }

    @GetMapping("/list")
    public ResponseEntity<ApiResponse<List<NutritionReport>>> getUserReports(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId) {
        User user = extractUser(authentication);
        if (user == null) return unauthorized();
        int operateAs = resolveOperateUserId(user.getUserId(), targetUserId);
        if (operateAs == -1) return forbidden("无权查看该用户的报告");
        List<NutritionReport> reports = reportService.getUserReports(operateAs);
        return ResponseEntity.ok(ApiResponse.success(reports));
    }

    @GetMapping("/range")
    public ResponseEntity<ApiResponse<List<NutritionReport>>> getReportsBetween(
            Authentication authentication,
            @RequestParam(name = "startDate") String startDate,
            @RequestParam(name = "endDate") String endDate,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId) {
        User user = extractUser(authentication);
        if (user == null) return unauthorized();
        int operateAs = resolveOperateUserId(user.getUserId(), targetUserId);
        if (operateAs == -1) return forbidden("无权查看该用户的报告");
        List<NutritionReport> reports = reportService.getUserReportsBetween(
                operateAs, LocalDate.parse(startDate), LocalDate.parse(endDate));
        return ResponseEntity.ok(ApiResponse.success(reports));
    }

    @DeleteMapping("/{reportId}")
    public ResponseEntity<ApiResponse<Void>> deleteReport(
            Authentication authentication,
            @PathVariable(name = "reportId") Integer reportId,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId) {
        User user = extractUser(authentication);
        if (user == null) return unauthorized();
        int operateAs = resolveOperateUserId(user.getUserId(), targetUserId);
        if (operateAs == -1) return forbidden("无权删除该用户的报告");
        reportService.deleteReport(reportId, operateAs);
        return ResponseEntity.ok(ApiResponse.success("报告已删除", null));
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

    private ResponseEntity unauthorized() {
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(ApiResponse.error("请先登录"));
    }

    private ResponseEntity forbidden(String msg) {
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(ApiResponse.error(msg));
    }
}
