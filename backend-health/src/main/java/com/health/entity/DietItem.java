package com.health.entity;

import javax.persistence.*;
import java.math.BigDecimal;

@Entity
@Table(name = "diet_item")
public class DietItem {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer itemId;

    @Column(name = "meal_id", nullable = false)
    private Integer mealId;

    @Column(name = "food_id", nullable = false)
    private Integer foodId;

    @Column(name = "eat_weight", nullable = false)
    private BigDecimal eatWeight;

    public DietItem() {}

    public Integer getItemId() { return itemId; }
    public void setItemId(Integer itemId) { this.itemId = itemId; }
    public Integer getMealId() { return mealId; }
    public void setMealId(Integer mealId) { this.mealId = mealId; }
    public Integer getFoodId() { return foodId; }
    public void setFoodId(Integer foodId) { this.foodId = foodId; }
    public BigDecimal getEatWeight() { return eatWeight; }
    public void setEatWeight(BigDecimal eatWeight) { this.eatWeight = eatWeight; }
}
