package com.health.dto;

import java.math.BigDecimal;

public class AddMealRequest {
    private String eatDate;
    private String mealType;
    private String remark;
    private java.util.List<MealItem> items;

    public AddMealRequest() {}

    public String getEatDate() { return eatDate; }
    public void setEatDate(String eatDate) { this.eatDate = eatDate; }
    public String getMealType() { return mealType; }
    public void setMealType(String mealType) { this.mealType = mealType; }
    public String getRemark() { return remark; }
    public void setRemark(String remark) { this.remark = remark; }
    public java.util.List<MealItem> getItems() { return items; }
    public void setItems(java.util.List<MealItem> items) { this.items = items; }

    public static class MealItem {
        private Integer foodId;
        private BigDecimal eatWeight;

        public MealItem() {}

        public Integer getFoodId() { return foodId; }
        public void setFoodId(Integer foodId) { this.foodId = foodId; }
        public BigDecimal getEatWeight() { return eatWeight; }
        public void setEatWeight(BigDecimal eatWeight) { this.eatWeight = eatWeight; }
    }
}
