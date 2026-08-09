package com.health.entity;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "diet_meal")
public class DietMeal {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer mealId;

    @Column(name = "user_id", nullable = false)
    private Integer userId;

    @Column(name = "eat_date", nullable = false)
    private String eatDate;

    @Column(name = "meal_type", nullable = false)
    private String mealType;

    @Column(name = "remark")
    private String remark;

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();

    public DietMeal() {}

    public Integer getMealId() { return mealId; }
    public void setMealId(Integer mealId) { this.mealId = mealId; }
    public Integer getUserId() { return userId; }
    public void setUserId(Integer userId) { this.userId = userId; }
    public String getEatDate() { return eatDate; }
    public void setEatDate(String eatDate) { this.eatDate = eatDate; }
    public String getMealType() { return mealType; }
    public void setMealType(String mealType) { this.mealType = mealType; }
    public String getRemark() { return remark; }
    public void setRemark(String remark) { this.remark = remark; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
