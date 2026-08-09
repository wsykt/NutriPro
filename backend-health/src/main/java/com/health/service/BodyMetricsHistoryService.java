package com.health.service;

import com.health.entity.BodyMetricsHistory;
import com.health.entity.User;
import com.health.repository.BodyMetricsHistoryRepository;
import com.health.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
public class BodyMetricsHistoryService {

    private final BodyMetricsHistoryRepository historyRepository;
    private final UserRepository userRepository;

    public BodyMetricsHistoryService(BodyMetricsHistoryRepository historyRepository,
                                      UserRepository userRepository) {
        this.historyRepository = historyRepository;
        this.userRepository = userRepository;
    }

    /**
     * 保存某个用户在指定日期的身体指标快照（不存在则插入，存在则更新）。
     */
    @Transactional
    public BodyMetricsHistory saveMetrics(Integer userId, String recordDate,
                                          Double height, Double weight, Integer age,
                                          Double bmr, String crowdType) {
        log.info("开始保存身体指标快照, userId={}, recordDate={}", userId, recordDate);
        Optional<BodyMetricsHistory> existing = historyRepository.findByUserIdAndRecordDate(userId, recordDate);
        BodyMetricsHistory history = existing.orElse(new BodyMetricsHistory());
        history.setUserId(userId);
        history.setRecordDate(recordDate);
        if (height != null) history.setHeight(height);
        if (weight != null) history.setWeight(weight);
        if (age != null) history.setAge(age);
        if (bmr != null) history.setBmr(bmr);
        if (crowdType != null) history.setCrowdType(crowdType);
        return historyRepository.save(history);
    }

    /**
     * 直接从当前用户资料里把身体指标快照到指定日期。
     */
    @Transactional
    public BodyMetricsHistory snapshotFromUser(Integer userId, LocalDate recordDate) {
        User user = userRepository.findById(userId).orElseThrow(() -> new RuntimeException("用户不存在"));
        return saveMetrics(
                userId,
                recordDate.toString(),
                user.getHeight(),
                user.getWeight(),
                user.getAge(),
                computeBmr(user),
                user.getCrowdType()
        );
    }

    public List<BodyMetricsHistory> getHistory(Integer userId) {
        return historyRepository.findByUserIdOrderByRecordDateDesc(userId);
    }

    public List<BodyMetricsHistory> getHistoryByRange(Integer userId, String startDate, String endDate) {
        return historyRepository.findByUserIdAndRecordDateBetweenOrderByRecordDateDesc(userId, startDate, endDate);
    }

    @Transactional
    public boolean deleteByDate(Integer userId, String recordDate) {
        Optional<BodyMetricsHistory> existing = historyRepository.findByUserIdAndRecordDate(userId, recordDate);
        if (!existing.isPresent()) return false;
        historyRepository.deleteByUserIdAndRecordDate(userId, recordDate);
        return true;
    }

    private Double computeBmr(User user) {
        if (user == null || user.getWeight() == null || user.getHeight() == null || user.getAge() == null) return null;
        double w = user.getWeight();
        double h = user.getHeight();
        int a = user.getAge();
        boolean isFemale = "女".equals(user.getGender());
        // Mifflin–St Jeor 简化公式
        double bmr = 10 * w + 6.25 * h - 5 * a + (isFemale ? -161 : 5);
        return Math.round(bmr * 10.0) / 10.0;
    }
}
