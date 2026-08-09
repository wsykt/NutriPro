package com.health.dto;

import java.math.BigDecimal;

public class FoodDTO {
    private Integer foodId;
    private String foodName;
    private String foodCategory;
    private BigDecimal calorie;
    private BigDecimal protein;
    private BigDecimal fat;
    private BigDecimal carb;
    private BigDecimal dietFiber;
    private BigDecimal giValue;
    private BigDecimal calcium;
    private BigDecimal dha;
    private BigDecimal folicAcid;
    private Integer showGi;
    private Integer showFolicAcid;
    private Integer showDha;

    public FoodDTO() {}

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
}
