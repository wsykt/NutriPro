package com.health.vo;

import com.health.entity.RecipeIngredient;

import java.math.BigDecimal;

public class RecipeIngredientVO {

    private Integer id;
    private String foodName;
    private BigDecimal rawWeight;
    private BigDecimal cookedWeight;
    private BigDecimal calories;
    private BigDecimal protein;
    private BigDecimal carbs;
    private BigDecimal fat;

    public RecipeIngredientVO() {}

    public static RecipeIngredientVO fromEntity(RecipeIngredient ingredient) {
        if (ingredient == null) return null;
        RecipeIngredientVO vo = new RecipeIngredientVO();
        vo.setId(ingredient.getIngredientId());
        vo.setFoodName(ingredient.getIngredientName());
        vo.setRawWeight(ingredient.getAmount());
        return vo;
    }

    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }
    public String getFoodName() { return foodName; }
    public void setFoodName(String foodName) { this.foodName = foodName; }
    public BigDecimal getRawWeight() { return rawWeight; }
    public void setRawWeight(BigDecimal rawWeight) { this.rawWeight = rawWeight; }
    public BigDecimal getCookedWeight() { return cookedWeight; }
    public void setCookedWeight(BigDecimal cookedWeight) { this.cookedWeight = cookedWeight; }
    public BigDecimal getCalories() { return calories; }
    public void setCalories(BigDecimal calories) { this.calories = calories; }
    public BigDecimal getProtein() { return protein; }
    public void setProtein(BigDecimal protein) { this.protein = protein; }
    public BigDecimal getCarbs() { return carbs; }
    public void setCarbs(BigDecimal carbs) { this.carbs = carbs; }
    public BigDecimal getFat() { return fat; }
    public void setFat(BigDecimal fat) { this.fat = fat; }
}
