package com.health.repository;

import com.health.entity.NutritionReport;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

@Repository
public interface NutritionReportRepository extends JpaRepository<NutritionReport, Integer> {
    Optional<NutritionReport> findByUserIdAndReportDate(Integer userId, LocalDate reportDate);
    List<NutritionReport> findByUserIdOrderByReportDateDesc(Integer userId);
    List<NutritionReport> findByUserIdAndReportDateBetweenOrderByReportDateDesc(Integer userId, LocalDate startDate, LocalDate endDate);
}