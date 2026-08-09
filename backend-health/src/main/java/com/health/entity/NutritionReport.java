package com.health.entity;

import javax.persistence.*;
import java.time.LocalDate;

@Entity
@Table(name = "nutrition_report")
public class NutritionReport {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer reportId;

    @Column(name = "user_id", nullable = false)
    private Integer userId;

    @Column(name = "report_date", nullable = false)
    private LocalDate reportDate;

    @Column(name = "total_calorie")
    private Double totalCalorie;

    @Column(name = "total_protein")
    private Double totalProtein;

    @Column(name = "total_fat")
    private Double totalFat;

    @Column(name = "total_carb")
    private Double totalCarb;

    @Column(name = "total_diet_fiber")
    private Double totalDietFiber;

    @Column(name = "total_calcium")
    private Double totalCalcium;

    @Column(name = "total_dha")
    private Double totalDha;

    @Column(name = "total_folic_acid")
    private Double totalFolicAcid;

    @Column(name = "bmr")
    private Double bmr;

    @Column(name = "intake_bmr_ratio")
    private Double intakeBmrRatio;

    @Column(name = "protein_status")
    private String proteinStatus;

    @Column(name = "fat_status")
    private String fatStatus;

    @Column(name = "carb_status")
    private String carbStatus;

    @Column(name = "calcium_status")
    private String calciumStatus;

    @Column(name = "folic_acid_status")
    private String folicAcidStatus;

    @Column(name = "diet_fiber_status")
    private String dietFiberStatus;

    @Column(name = "dha_status")
    private String dhaStatus;

    @Column(name = "crowd_type")
    private String crowdType;

    // —— 生成报告时的身体指标快照（来自用户资料） ——
    @Column(name = "user_height")
    private Double userHeight;

    @Column(name = "user_weight")
    private Double userWeight;

    @Column(name = "user_age")
    private Integer userAge;

    @Column(name = "user_bmr")
    private Double userBmr;

    @Column(name = "user_crowd_type")
    private String userCrowdType;

    public NutritionReport() {}

    public Integer getReportId() { return reportId; }
    public void setReportId(Integer reportId) { this.reportId = reportId; }
    public Integer getUserId() { return userId; }
    public void setUserId(Integer userId) { this.userId = userId; }
    public LocalDate getReportDate() { return reportDate; }
    public void setReportDate(LocalDate reportDate) { this.reportDate = reportDate; }
    public Double getTotalCalorie() { return totalCalorie; }
    public void setTotalCalorie(Double totalCalorie) { this.totalCalorie = totalCalorie; }
    public Double getTotalProtein() { return totalProtein; }
    public void setTotalProtein(Double totalProtein) { this.totalProtein = totalProtein; }
    public Double getTotalFat() { return totalFat; }
    public void setTotalFat(Double totalFat) { this.totalFat = totalFat; }
    public Double getTotalCarb() { return totalCarb; }
    public void setTotalCarb(Double totalCarb) { this.totalCarb = totalCarb; }
    public Double getTotalDietFiber() { return totalDietFiber; }
    public void setTotalDietFiber(Double totalDietFiber) { this.totalDietFiber = totalDietFiber; }
    public Double getTotalCalcium() { return totalCalcium; }
    public void setTotalCalcium(Double totalCalcium) { this.totalCalcium = totalCalcium; }
    public Double getTotalDha() { return totalDha; }
    public void setTotalDha(Double totalDha) { this.totalDha = totalDha; }
    public Double getTotalFolicAcid() { return totalFolicAcid; }
    public void setTotalFolicAcid(Double totalFolicAcid) { this.totalFolicAcid = totalFolicAcid; }
    public Double getBmr() { return bmr; }
    public void setBmr(Double bmr) { this.bmr = bmr; }
    public Double getIntakeBmrRatio() { return intakeBmrRatio; }
    public void setIntakeBmrRatio(Double intakeBmrRatio) { this.intakeBmrRatio = intakeBmrRatio; }
    public String getProteinStatus() { return proteinStatus; }
    public void setProteinStatus(String proteinStatus) { this.proteinStatus = proteinStatus; }
    public String getFatStatus() { return fatStatus; }
    public void setFatStatus(String fatStatus) { this.fatStatus = fatStatus; }
    public String getCarbStatus() { return carbStatus; }
    public void setCarbStatus(String carbStatus) { this.carbStatus = carbStatus; }
    public String getCalciumStatus() { return calciumStatus; }
    public void setCalciumStatus(String calciumStatus) { this.calciumStatus = calciumStatus; }
    public String getFolicAcidStatus() { return folicAcidStatus; }
    public void setFolicAcidStatus(String folicAcidStatus) { this.folicAcidStatus = folicAcidStatus; }
    public String getDietFiberStatus() { return dietFiberStatus; }
    public void setDietFiberStatus(String dietFiberStatus) { this.dietFiberStatus = dietFiberStatus; }
    public String getDhaStatus() { return dhaStatus; }
    public void setDhaStatus(String dhaStatus) { this.dhaStatus = dhaStatus; }
    public String getCrowdType() { return crowdType; }
    public void setCrowdType(String crowdType) { this.crowdType = crowdType; }

    public Double getUserHeight() { return userHeight; }
    public void setUserHeight(Double userHeight) { this.userHeight = userHeight; }

    public Double getUserWeight() { return userWeight; }
    public void setUserWeight(Double userWeight) { this.userWeight = userWeight; }

    public Integer getUserAge() { return userAge; }
    public void setUserAge(Integer userAge) { this.userAge = userAge; }

    public Double getUserBmr() { return userBmr; }
    public void setUserBmr(Double userBmr) { this.userBmr = userBmr; }

    public String getUserCrowdType() { return userCrowdType; }
    public void setUserCrowdType(String userCrowdType) { this.userCrowdType = userCrowdType; }
}