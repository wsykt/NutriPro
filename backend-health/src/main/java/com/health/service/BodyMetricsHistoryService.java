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

    /**
     * 健康时序预测：基于历史体重序列做简单线性回归，预测未来 days 天的体重趋势。
     * 返回预测点（日期 + 预测体重 + 区间），以及趋势方向与说明。
     */
    public java.util.Map<String, Object> predictWeightTrend(Integer userId, int days) {
        List<BodyMetricsHistory> desc = historyRepository.findByUserIdOrderByRecordDateDesc(userId);
        List<BodyMetricsHistory> asc = new java.util.ArrayList<>(desc);
        java.util.Collections.reverse(asc);

        java.util.Map<String, Object> result = new java.util.LinkedHashMap<>();
        List<java.util.Map<String, Object>> points = new java.util.ArrayList<>();
        result.put("metric", "weight");
        result.put("unit", "kg");
        result.put("days", days);
        result.put("points", points);

        // 提取有效体重序列（至少 2 个点才可回归）
        List<Double> weights = new java.util.ArrayList<>();
        for (BodyMetricsHistory h : asc) {
            if (h.getWeight() != null) weights.add(h.getWeight());
        }
        int n = weights.size();
        if (n < 2) {
            result.put("status", "insufficient_data");
            result.put("message", "至少需要 2 条带体重的历史记录才能预测");
            return result;
        }

        // 简单线性回归 y = a + b*x（x = 相对首日的天数序号）
        double sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
        for (int i = 0; i < n; i++) {
            double x = i, y = weights.get(i);
            sumX += x; sumY += y; sumXY += x * y; sumX2 += x * x;
        }
        double b = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
        double a = (sumY - b * sumX) / n;

        // 残差标准差（用于置信区间）
        double sse = 0;
        for (int i = 0; i < n; i++) {
            double y = weights.get(i), pred = a + b * i;
            sse += (y - pred) * (y - pred);
        }
        double sd = Math.sqrt(sse / Math.max(1, n - 2));

        // 预测未来 days 天
        LocalDate lastDate = LocalDate.parse(asc.get(asc.size() - 1).getRecordDate());
        for (int d = 1; d <= days; d++) {
            double x = n - 1 + d;
            double pred = a + b * x;
            double width = 1.96 * sd * (1 + d / 3.0); // 置信带随预测距离放宽
            java.util.Map<String, Object> p = new java.util.LinkedHashMap<>();
            p.put("date", lastDate.plusDays(d).toString());
            p.put("predictedWeight", Math.round(pred * 10.0) / 10.0);
            p.put("lower", Math.round((pred - width) * 10.0) / 10.0);
            p.put("upper", Math.round((pred + width) * 10.0) / 10.0);
            points.add(p);
        }

        // 趋势判断
        double weeklyChange = b * 7;
        String trend = Math.abs(weeklyChange) < 0.3 ? "stable"
                : (weeklyChange < 0 ? "down" : "up");
        String trendText = "stable".equals(trend) ? "体重趋于平稳"
                : "down".equals(trend) ? "预计体重缓慢下降（周变化约 " + String.format("%.1f", weeklyChange) + " kg）"
                : "预计体重缓慢上升（周变化约 " + String.format("%.1f", weeklyChange) + " kg）";
        result.put("status", "ok");
        result.put("trend", trend);
        result.put("message", trendText);
        result.put("sampleSize", n);
        return result;
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
