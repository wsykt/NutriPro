package com.health.controller;

import com.health.dto.ApiResponse;
import com.health.entity.ExerciseRecord;
import com.health.entity.User;
import com.health.service.ExerciseRecordService;
import com.health.service.FamilyRelationService;
import com.health.service.ProfileService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/exercise")
@CrossOrigin
public class ExerciseRecordController {

    private final ProfileService profileService;
    private final FamilyRelationService familyRelationService;
    private final ExerciseRecordService exerciseRecordService;

    public ExerciseRecordController(ProfileService profileService,
                                    FamilyRelationService familyRelationService,
                                    ExerciseRecordService exerciseRecordService) {
        this.profileService = profileService;
        this.familyRelationService = familyRelationService;
        this.exerciseRecordService = exerciseRecordService;
    }

    private User extractUser(Authentication authentication) {
        if (authentication == null) return null;
        if (authentication.getPrincipal() instanceof User) {
            return (User) authentication.getPrincipal();
        }
        try {
            return profileService.findByUsername(authentication.getName());
        } catch (Exception e) {
            return null;
        }
    }

    private int resolveOperateUserId(int currentUserId, Integer targetUserId) {
        if (targetUserId == null || targetUserId == currentUserId) return currentUserId;
        if (familyRelationService.isConfirmedGuardian(currentUserId, targetUserId)) return targetUserId;
        return -1;
    }

    @PostMapping("/add")
    public ResponseEntity<ApiResponse<ExerciseRecord>> addRecord(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId,
            @RequestBody Map<String, Object> body) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        int targetId = resolveOperateUserId(current.getUserId(), targetUserId);
        if (targetId == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权操作该用户"));
        }

        String exerciseType = body != null ? String.valueOf(body.getOrDefault("exerciseType", "")).trim() : "";
        Integer durationMin = body != null && body.get("durationMin") != null ? Integer.parseInt(String.valueOf(body.get("durationMin"))) : null;
        String note = body != null ? String.valueOf(body.getOrDefault("note", "")).trim() : "";

        if (exerciseType.isEmpty()) {
            return ResponseEntity.badRequest().body(ApiResponse.error(400, "请选择运动类型"));
        }
        if (durationMin == null || durationMin <= 0) {
            return ResponseEntity.badRequest().body(ApiResponse.error(400, "请输入有效的运动时长"));
        }

        ExerciseRecord record = exerciseRecordService.addRecord(targetId, exerciseType, durationMin, note);
        return ResponseEntity.ok(ApiResponse.success("运动记录已添加", record));
    }

    @PostMapping("/add-with-date")
    public ResponseEntity<ApiResponse<ExerciseRecord>> addRecordWithDate(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId,
            @RequestBody Map<String, Object> body) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        int targetId = resolveOperateUserId(current.getUserId(), targetUserId);
        if (targetId == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权操作该用户"));
        }

        String exerciseType = body != null ? String.valueOf(body.getOrDefault("exerciseType", "")).trim() : "";
        Integer durationMin = body != null && body.get("durationMin") != null ? Integer.parseInt(String.valueOf(body.get("durationMin"))) : null;
        String note = body != null ? String.valueOf(body.getOrDefault("note", "")).trim() : "";
        String dateStr = body != null ? String.valueOf(body.getOrDefault("recordDate", "")).trim() : "";

        if (exerciseType.isEmpty()) {
            return ResponseEntity.badRequest().body(ApiResponse.error(400, "请选择运动类型"));
        }
        if (durationMin == null || durationMin <= 0) {
            return ResponseEntity.badRequest().body(ApiResponse.error(400, "请输入有效的运动时长"));
        }

        LocalDate recordDate = dateStr.isEmpty() ? LocalDate.now() : LocalDate.parse(dateStr);
        ExerciseRecord record = exerciseRecordService.addRecordWithDate(targetId, exerciseType, durationMin, note, recordDate);
        return ResponseEntity.ok(ApiResponse.success("运动记录已添加", record));
    }

    @GetMapping("/records")
    public ResponseEntity<ApiResponse<List<ExerciseRecord>>> getRecords(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        int targetId = resolveOperateUserId(current.getUserId(), targetUserId);
        if (targetId == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权操作该用户"));
        }

        List<ExerciseRecord> records = exerciseRecordService.getRecords(targetId);
        return ResponseEntity.ok(ApiResponse.success(records));
    }

    @GetMapping("/records/today")
    public ResponseEntity<ApiResponse<List<ExerciseRecord>>> getTodayRecords(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        int targetId = resolveOperateUserId(current.getUserId(), targetUserId);
        if (targetId == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权操作该用户"));
        }

        List<ExerciseRecord> records = exerciseRecordService.getRecordsByDate(targetId, LocalDate.now());
        return ResponseEntity.ok(ApiResponse.success(records));
    }

    @GetMapping("/records/range")
    public ResponseEntity<ApiResponse<List<ExerciseRecord>>> getRecordsByRange(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId,
            @RequestParam String startDate,
            @RequestParam String endDate) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        int targetId = resolveOperateUserId(current.getUserId(), targetUserId);
        if (targetId == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权操作该用户"));
        }

        List<ExerciseRecord> records = exerciseRecordService.getRecordsByRange(
                targetId, LocalDate.parse(startDate), LocalDate.parse(endDate));
        return ResponseEntity.ok(ApiResponse.success(records));
    }

    @GetMapping("/stats/today")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getTodayStats(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        int targetId = resolveOperateUserId(current.getUserId(), targetUserId);
        if (targetId == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权操作该用户"));
        }

        Map<String, Object> stats = exerciseRecordService.getTodayStats(targetId);
        return ResponseEntity.ok(ApiResponse.success(stats));
    }

    @GetMapping("/stats/week")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getWeekStats(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        int targetId = resolveOperateUserId(current.getUserId(), targetUserId);
        if (targetId == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权操作该用户"));
        }

        Map<String, Object> stats = exerciseRecordService.getWeekStats(targetId);
        return ResponseEntity.ok(ApiResponse.success(stats));
    }

    @DeleteMapping("/record/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteRecord(
            Authentication authentication,
            @RequestParam(name = "targetUserId", required = false) Integer targetUserId,
            @PathVariable Integer id) {

        User current = extractUser(authentication);
        if (current == null || current.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        int targetId = resolveOperateUserId(current.getUserId(), targetUserId);
        if (targetId == -1) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权操作该用户"));
        }

        exerciseRecordService.deleteRecord(targetId, id);
        return ResponseEntity.ok(ApiResponse.success("运动记录已删除", null));
    }

    @GetMapping("/types")
    public ResponseEntity<ApiResponse<List<Map<String, Object>>>> getExerciseTypes() {
        List<Map<String, Object>> types = new java.util.ArrayList<>();
        types.add(createExerciseType("跑步", 8.0));
        types.add(createExerciseType("慢跑", 5.0));
        types.add(createExerciseType("游泳", 8.0));
        types.add(createExerciseType("骑行", 6.0));
        types.add(createExerciseType("力量训练", 5.0));
        types.add(createExerciseType("瑜伽", 3.0));
        types.add(createExerciseType("徒步", 4.0));
        types.add(createExerciseType("跳绳", 10.0));
        types.add(createExerciseType("篮球", 7.0));
        types.add(createExerciseType("羽毛球", 5.5));
        types.add(createExerciseType("乒乓球", 4.0));
        types.add(createExerciseType("舞蹈", 4.5));
        types.add(createExerciseType("快走", 3.5));
        types.add(createExerciseType("爬山", 6.0));
        types.add(createExerciseType("太极", 2.5));
        return ResponseEntity.ok(ApiResponse.success(types));
    }

    private Map<String, Object> createExerciseType(String label, double metValue) {
        Map<String, Object> map = new java.util.HashMap<>();
        map.put("label", label);
        map.put("metValue", metValue);
        return map;
    }
}
