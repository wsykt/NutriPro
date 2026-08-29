package com.health.service;

import com.health.entity.ExerciseRecord;
import com.health.entity.User;
import com.health.repository.ExerciseRecordRepository;
import com.health.repository.UserRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
public class ExerciseRecordService {

    private final ExerciseRecordRepository exerciseRecordRepository;
    private final UserRepository userRepository;

    public ExerciseRecordService(ExerciseRecordRepository exerciseRecordRepository, UserRepository userRepository) {
        this.exerciseRecordRepository = exerciseRecordRepository;
        this.userRepository = userRepository;
    }

    private static final Map<String, Double> EXERCISE_MET_MAP;
    static {
        Map<String, Double> map = new java.util.LinkedHashMap<>();
        map.put("跑步", 8.0);
        map.put("慢跑", 5.0);
        map.put("游泳", 8.0);
        map.put("骑行", 6.0);
        map.put("力量训练", 5.0);
        map.put("瑜伽", 3.0);
        map.put("徒步", 4.0);
        map.put("跳绳", 10.0);
        map.put("篮球", 7.0);
        map.put("羽毛球", 5.5);
        map.put("乒乓球", 4.0);
        map.put("舞蹈", 4.5);
        map.put("快走", 3.5);
        map.put("爬山", 6.0);
        map.put("太极", 2.5);
        EXERCISE_MET_MAP = java.util.Collections.unmodifiableMap(map);
    }

    public double calculateCalories(String exerciseType, int durationMin, double weightKg) {
        double met = EXERCISE_MET_MAP.getOrDefault(exerciseType, 5.0);
        return Math.round((met * 3.5 * weightKg * durationMin) / 200.0);
    }

    public ExerciseRecord addRecord(Integer userId, String exerciseType, Integer durationMin, String note) {
        log.info("开始记录运动, userId={}, exerciseType={}, durationMin={}", userId, exerciseType, durationMin);
        User user = userRepository.findById(userId).orElse(null);
        double weight = user != null && user.getWeight() != null ? user.getWeight() : 65.0;

        ExerciseRecord record = new ExerciseRecord();
        record.setUserId(userId);
        record.setExerciseType(exerciseType);
        record.setDurationMin(durationMin);
        record.setCaloriesBurned(calculateCalories(exerciseType, durationMin, weight));
        record.setRecordDate(LocalDate.now());
        record.setNote(note);
        // 用户自记录直接生效（approved），避免"新增后必须等管理员审核"造成周报/统计/AI 上下文空数据
        record.setStatus("approved");

        return exerciseRecordRepository.save(record);
    }

    public ExerciseRecord addRecordWithDate(Integer userId, String exerciseType, Integer durationMin, String note, LocalDate recordDate) {
        User user = userRepository.findById(userId).orElse(null);
        double weight = user != null && user.getWeight() != null ? user.getWeight() : 65.0;

        ExerciseRecord record = new ExerciseRecord();
        record.setUserId(userId);
        record.setExerciseType(exerciseType);
        record.setDurationMin(durationMin);
        record.setCaloriesBurned(calculateCalories(exerciseType, durationMin, weight));
        record.setRecordDate(recordDate != null ? recordDate : LocalDate.now());
        record.setNote(note);
        // 用户自记录直接生效（approved），避免"新增后必须等管理员审核"造成周报/统计/AI 上下文空数据
        record.setStatus("approved");

        return exerciseRecordRepository.save(record);
    }

    public List<ExerciseRecord> getRecords(Integer userId) {
        return exerciseRecordRepository.findByUserIdOrderByRecordDateDesc(userId).stream()
                .filter(r -> "approved".equals(r.getStatus()))
                .collect(java.util.stream.Collectors.toList());
    }

    public List<ExerciseRecord> getRecordsByDate(Integer userId, LocalDate date) {
        return exerciseRecordRepository.findByUserIdAndRecordDate(userId, date).stream()
                .filter(r -> "approved".equals(r.getStatus()))
                .collect(java.util.stream.Collectors.toList());
    }

    public List<ExerciseRecord> getRecordsByRange(Integer userId, LocalDate startDate, LocalDate endDate) {
        return exerciseRecordRepository.findByUserIdAndRecordDateBetweenOrderByRecordDateDesc(userId, startDate, endDate).stream()
                .filter(r -> "approved".equals(r.getStatus()))
                .collect(java.util.stream.Collectors.toList());
    }

    public void deleteRecord(Integer userId, Integer recordId) {
        ExerciseRecord record = exerciseRecordRepository.findById(recordId).orElse(null);
        if (record != null && record.getUserId().equals(userId)) {
            exerciseRecordRepository.delete(record);
        }
    }

    public Map<String, Object> getTodayStats(Integer userId) {
        LocalDate today = LocalDate.now();
        List<ExerciseRecord> todayRecords = exerciseRecordRepository.findByUserIdAndRecordDate(userId, today).stream()
                .filter(r -> "approved".equals(r.getStatus()))
                .collect(java.util.stream.Collectors.toList());

        int totalMinutes = todayRecords.stream().mapToInt(ExerciseRecord::getDurationMin).sum();
        double totalCalories = todayRecords.stream().mapToDouble(r -> r.getCaloriesBurned() != null ? r.getCaloriesBurned() : 0).sum();

        Map<String, Object> map = new java.util.LinkedHashMap<>();
        map.put("duration", totalMinutes);
        map.put("calories", totalCalories);
        map.put("recordCount", todayRecords.size());
        return map;
    }

    public Map<String, Object> getWeekStats(Integer userId) {
        LocalDate endDate = LocalDate.now();
        LocalDate startDate = endDate.minusDays(6);
        List<ExerciseRecord> weekRecords = exerciseRecordRepository.findByUserIdAndRecordDateBetweenOrderByRecordDateDesc(userId, startDate, endDate).stream()
                .filter(r -> "approved".equals(r.getStatus()))
                .collect(java.util.stream.Collectors.toList());

        int count = weekRecords.size();
        double totalCalories = weekRecords.stream().mapToDouble(r -> r.getCaloriesBurned() != null ? r.getCaloriesBurned() : 0).sum();

        Map<String, Object> map = new java.util.LinkedHashMap<>();
        map.put("count", count);
        map.put("totalCalories", totalCalories);
        return map;
    }

    public List<ExerciseRecord> getAllRecords() {
        return exerciseRecordRepository.findAll();
    }

    public List<ExerciseRecord> getRecordsByStatus(String status) {
        return exerciseRecordRepository.findByStatus(status);
    }

    public ExerciseRecord approveRecord(Integer recordId) {
        ExerciseRecord record = exerciseRecordRepository.findById(recordId).orElse(null);
        if (record != null) {
            record.setStatus("approved");
            return exerciseRecordRepository.save(record);
        }
        return null;
    }

    public ExerciseRecord rejectRecord(Integer recordId) {
        ExerciseRecord record = exerciseRecordRepository.findById(recordId).orElse(null);
        if (record != null) {
            record.setStatus("rejected");
            return exerciseRecordRepository.save(record);
        }
        return null;
    }

    public void deleteRecordById(Integer recordId) {
        exerciseRecordRepository.deleteById(recordId);
    }
}
