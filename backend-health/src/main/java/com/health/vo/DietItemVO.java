package com.health.vo;

import com.health.entity.DietItem;
import com.health.entity.Food;

import java.math.BigDecimal;

public class DietItemVO {

    private Integer id;
    private String foodName;
    private BigDecimal quantity;
    private String unit;
    private BigDecimal calories;
    private BigDecimal protein;
    private BigDecimal carbs;
    private BigDecimal fat;

    public DietItemVO() {}

    public static DietItemVO fromEntity(DietItem item, Food food) {
        DietItemVO vo = new DietItemVO();
        vo.setId(item.getItemId());
        if (food != null) {
            vo.setFoodName(food.getFoodName());
            vo.setCalories(food.getCalorie());
            vo.setProtein(food.getProtein());
            vo.setCarbs(food.getCarb());
            vo.setFat(food.getFat());
        }
        vo.setQuantity(item.getEatWeight());
        vo.setUnit("g");
        return vo;
    }

    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }
    public String getFoodName() { return foodName; }
    public void setFoodName(String foodName) { this.foodName = foodName; }
    public BigDecimal getQuantity() { return quantity; }
    public void setQuantity(BigDecimal quantity) { this.quantity = quantity; }
    public String getUnit() { return unit; }
    public void setUnit(String unit) { this.unit = unit; }
    public BigDecimal getCalories() { return calories; }
    public void setCalories(BigDecimal calories) { this.calories = calories; }
    public BigDecimal getProtein() { return protein; }
    public void setProtein(BigDecimal protein) { this.protein = protein; }
    public BigDecimal getCarbs() { return carbs; }
    public void setCarbs(BigDecimal carbs) { this.carbs = carbs; }
    public BigDecimal getFat() { return fat; }
    public void setFat(BigDecimal fat) { this.fat = fat; }
}
