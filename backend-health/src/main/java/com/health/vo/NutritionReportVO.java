package com.health.vo;

import com.health.entity.NutritionReport;

import java.time.LocalDate;
import java.time.LocalDateTime;

public class NutritionReportVO {

    private Integer id;
    private LocalDate reportDate;
    private Double totalCalories;
    private Double totalProtein;
    private Double totalCarbs;
    private Double totalFat;
    private Double calcium;
    private Double folicAcid;
    private Double dha;
    private Double dietFiber;
    private Double bmr;
    private Double bmrRatio;
    private String bmrStatus;
    private String recommendations;
    private LocalDateTime createdAt;

    public NutritionReportVO() {}

    public static NutritionReportVO fromEntity(NutritionReport report) {
        if (report == null) return null;
        NutritionReportVO vo = new NutritionReportVO();
        vo.setId(report.getReportId());
        vo.setReportDate(report.getReportDate());
        vo.setTotalCalories(report.getTotalCalorie());
        vo.setTotalProtein(report.getTotalProtein());
        vo.setTotalCarbs(report.getTotalCarb());
        vo.setTotalFat(report.getTotalFat());
        vo.setCalcium(report.getTotalCalcium());
        vo.setFolicAcid(report.getTotalFolicAcid());
        vo.setDha(report.getTotalDha());
        vo.setDietFiber(report.getTotalDietFiber());
        vo.setBmr(report.getBmr());
        vo.setBmrRatio(report.getIntakeBmrRatio());
        return vo;
    }

    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }
    public LocalDate getReportDate() { return reportDate; }
    public void setReportDate(LocalDate reportDate) { this.reportDate = reportDate; }
    public Double getTotalCalories() { return totalCalories; }
    public void setTotalCalories(Double totalCalories) { this.totalCalories = totalCalories; }
    public Double getTotalProtein() { return totalProtein; }
    public void setTotalProtein(Double totalProtein) { this.totalProtein = totalProtein; }
    public Double getTotalCarbs() { return totalCarbs; }
    public void setTotalCarbs(Double totalCarbs) { this.totalCarbs = totalCarbs; }
    public Double getTotalFat() { return totalFat; }
    public void setTotalFat(Double totalFat) { this.totalFat = totalFat; }
    public Double getCalcium() { return calcium; }
    public void setCalcium(Double calcium) { this.calcium = calcium; }
    public Double getFolicAcid() { return folicAcid; }
    public void setFolicAcid(Double folicAcid) { this.folicAcid = folicAcid; }
    public Double getDha() { return dha; }
    public void setDha(Double dha) { this.dha = dha; }
    public Double getDietFiber() { return dietFiber; }
    public void setDietFiber(Double dietFiber) { this.dietFiber = dietFiber; }
    public Double getBmr() { return bmr; }
    public void setBmr(Double bmr) { this.bmr = bmr; }
    public Double getBmrRatio() { return bmrRatio; }
    public void setBmrRatio(Double bmrRatio) { this.bmrRatio = bmrRatio; }
    public String getBmrStatus() { return bmrStatus; }
    public void setBmrStatus(String bmrStatus) { this.bmrStatus = bmrStatus; }
    public String getRecommendations() { return recommendations; }
    public void setRecommendations(String recommendations) { this.recommendations = recommendations; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
