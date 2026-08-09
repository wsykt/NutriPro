package com.health.entity;

import javax.persistence.*;
import java.math.BigDecimal;

@Entity
@Table(name = "food")
public class Food {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer foodId;

    @Column(name = "food_name", nullable = false)
    private String foodName;

    @Column(name = "food_category", nullable = false)
    private String foodCategory;

    @Column(name = "calorie")
    private BigDecimal calorie;

    @Column(name = "protein")
    private BigDecimal protein;

    @Column(name = "fat")
    private BigDecimal fat;

    @Column(name = "carb")
    private BigDecimal carb;

    @Column(name = "diet_fiber")
    private BigDecimal dietFiber;

    @Column(name = "gi_value")
    private BigDecimal giValue;

    @Column(name = "calcium")
    private BigDecimal calcium;

    @Column(name = "dha")
    private BigDecimal dha;

    @Column(name = "folic_acid")
    private BigDecimal folicAcid;

    @Column(name = "show_gi", columnDefinition = "INTEGER DEFAULT 0")
    private Integer showGi;

    @Column(name = "show_folic_acid", columnDefinition = "INTEGER DEFAULT 0")
    private Integer showFolicAcid;

    @Column(name = "show_dha", columnDefinition = "INTEGER DEFAULT 0")
    private Integer showDha;

    @Column(name = "status", columnDefinition = "TEXT DEFAULT 'approved'")
    private String status = "approved";

    @Column(name = "priority", columnDefinition = "INTEGER DEFAULT 0")
    private Integer priority = 0;

    public Food() {}

    public Integer getFoodId() { return foodId; }
    public void setFoodId(Integer foodId) { this.foodId = foodId; }
    public String getFoodName() { return foodName; }
    public void setFoodName(String foodName) { this.foodName = foodName; }
    public String getFoodCategory() { return foodCategory; }
    public void setFoodCategory(String foodCategory) { this.foodCategory = foodCategory; }
    public BigDecimal getCalorie() { return calorie; }
    public void setCalorie(BigDecimal calorie) { this.calorie = calorie; }
    public BigDecimal getProtein() { return protein; }
    public void setProtein(BigDecimal protein) { this.protein = protein; }
    public BigDecimal getFat() { return fat; }
    public void setFat(BigDecimal fat) { this.fat = fat; }
    public BigDecimal getCarb() { return carb; }
    public void setCarb(BigDecimal carb) { this.carb = carb; }
    public BigDecimal getDietFiber() { return dietFiber; }
    public void setDietFiber(BigDecimal dietFiber) { this.dietFiber = dietFiber; }
    public BigDecimal getGiValue() { return giValue; }
    public void setGiValue(BigDecimal giValue) { this.giValue = giValue; }
    public BigDecimal getCalcium() { return calcium; }
    public void setCalcium(BigDecimal calcium) { this.calcium = calcium; }
    public BigDecimal getDha() { return dha; }
    public void setDha(BigDecimal dha) { this.dha = dha; }
    public BigDecimal getFolicAcid() { return folicAcid; }
    public void setFolicAcid(BigDecimal folicAcid) { this.folicAcid = folicAcid; }
    public Integer getShowGi() { return showGi; }
    public void setShowGi(Integer showGi) { this.showGi = showGi; }
    public Integer getShowFolicAcid() { return showFolicAcid; }
    public void setShowFolicAcid(Integer showFolicAcid) { this.showFolicAcid = showFolicAcid; }
    public Integer getShowDha() { return showDha; }
    public void setShowDha(Integer showDha) { this.showDha = showDha; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Integer getPriority() { return priority; }
    public void setPriority(Integer priority) { this.priority = priority; }
}
