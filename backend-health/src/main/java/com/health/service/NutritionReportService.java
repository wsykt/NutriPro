package com.health.service;

import com.health.entity.NutritionReport;
import com.health.entity.User;
import com.health.repository.NutritionReportRepository;
import com.health.repository.UserRepository;
import com.health.util.NutritionCalculator;
import com.health.vo.NutritionReportVO;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
public class NutritionReportService {

    private final NutritionReportRepository reportRepository;
    private final UserRepository userRepository;

    public NutritionReportService(NutritionReportRepository reportRepository, UserRepository userRepository) {
        this.reportRepository = reportRepository;
        this.userRepository = userRepository;
    }

    @Transactional
    public NutritionReport saveReport(Integer userId, Map<String, Object> analysisData) {
        log.info("开始保存营养报告, userId={}, reportDate={}", userId, analysisData.get("reportDate"));
        User user = userRepository.findById(userId).orElseThrow(() -> new RuntimeException("用户不存在"));
        LocalDate reportDate = LocalDate.parse((String) analysisData.get("reportDate"));

        Optional<NutritionReport> existing = reportRepository.findByUserIdAndReportDate(userId, reportDate);
        NutritionReport report = existing.orElse(new NutritionReport());

        report.setUserId(userId);
        report.setReportDate(reportDate);
        report.setCrowdType(user.getCrowdType());
        // 同时写入身体指标快照，便于前端查询报告时一并展示
        report.setUserHeight(user.getHeight());
        report.setUserWeight(user.getWeight());
        report.setUserAge(user.getAge());
        report.setUserCrowdType(user.getCrowdType());
        try {
            double bmr = NutritionCalculator.calculateBMR(user.getWeight(), user.getHeight(), user.getAge(), user.getGender());
            report.setUserBmr(bmr);
            if (report.getBmr() == null) report.setBmr(bmr);
        } catch (Exception ignore) {}

        @SuppressWarnings("unchecked")
        Map<String, Object> total = (Map<String, Object>) analysisData.get("total");
        if (total != null) {
            report.setTotalCalorie(toDouble(total.get("calorie")));
            report.setTotalProtein(toDouble(total.get("protein")));
            report.setTotalFat(toDouble(total.get("fat")));
            report.setTotalCarb(toDouble(total.get("carb")));
            report.setTotalDietFiber(toDouble(total.get("dietFiber")));
            report.setTotalCalcium(toDouble(total.get("calcium")));
            report.setTotalDha(toDouble(total.get("dna")));
            report.setTotalFolicAcid(toDouble(total.get("folicAcid")));
        }

        @SuppressWarnings("unchecked")
        Map<String, Object> userMap = (Map<String, Object>) analysisData.get("user");
        if (userMap != null) {
            report.setBmr(toDouble(userMap.get("bmr")));
            report.setIntakeBmrRatio(toDouble(userMap.get("intakeBmrRatio")));
        }

        @SuppressWarnings("unchecked")
        Map<String, Object> status = (Map<String, Object>) analysisData.get("status");
        if (status != null) {
            report.setProteinStatus((String) status.get("protein"));
            report.setFatStatus((String) status.get("fat"));
            report.setCarbStatus((String) status.get("carb"));
            report.setCalciumStatus((String) status.get("calcium"));
            report.setFolicAcidStatus((String) status.get("folicAcid"));
            report.setDietFiberStatus((String) status.get("dietFiber"));
            report.setDhaStatus((String) status.get("dha"));
        }

        return reportRepository.save(report);
    }

    public Optional<NutritionReport> getReportByDate(Integer userId, LocalDate date) {
        return reportRepository.findByUserIdAndReportDate(userId, date);
    }

    public List<NutritionReport> getUserReports(Integer userId) {
        return reportRepository.findByUserIdOrderByReportDateDesc(userId);
    }

    public List<NutritionReportVO> getUserReportsVO(Integer userId) {
        List<NutritionReport> reports = reportRepository.findByUserIdOrderByReportDateDesc(userId);
        return reports.stream().map(NutritionReportVO::fromEntity).collect(Collectors.toList());
    }

    public List<NutritionReport> getUserReportsBetween(Integer userId, LocalDate startDate, LocalDate endDate) {
        return reportRepository.findByUserIdAndReportDateBetweenOrderByReportDateDesc(userId, startDate, endDate);
    }

    @Transactional
    public void deleteReport(Integer reportId, Integer userId) {
        NutritionReport report = reportRepository.findById(reportId)
                .orElseThrow(() -> new RuntimeException("报告不存在"));
        if (!report.getUserId().equals(userId)) {
            throw new RuntimeException("无权删除此报告");
        }
        reportRepository.delete(report);
    }

    private Double toDouble(Object value) {
        if (value == null) return null;
        if (value instanceof BigDecimal) {
            return ((BigDecimal) value).doubleValue();
        }
        if (value instanceof Number) {
            return ((Number) value).doubleValue();
        }
        try {
            return Double.parseDouble(value.toString());
        } catch (NumberFormatException e) {
            return null;
        }
    }


}