package com.health.vo;

import com.health.entity.DietItem;
import com.health.entity.DietMeal;
import com.health.entity.Food;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

public class DietMealVO {

    private Integer id;
    private String mealDate;
    private String mealType;
    private BigDecimal totalCalories;
    private LocalDateTime createdAt;
    private List<DietItemVO> items;

    public DietMealVO() {}

    /**
     * @param meal  餐次实体
     * @param items 该餐次下的饮食条目（需要与 food 关联后传入）
     */
    public static DietMealVO fromEntity(DietMeal meal, List<DietItem> items, List<Food> foods) {
        DietMealVO vo = new DietMealVO();
        vo.setId(meal.getMealId());
        vo.setMealDate(meal.getEatDate());
        vo.setMealType(meal.getMealType());
        vo.setCreatedAt(meal.getCreatedAt());

        List<DietItemVO> itemVOs = new ArrayList<>();
        BigDecimal totalCal = BigDecimal.ZERO;
        if (items != null && foods != null) {
            for (DietItem item : items) {
                Food matched = foods.stream()
                        .filter(f -> f.getFoodId().equals(item.getFoodId()))
                        .findFirst().orElse(null);
                DietItemVO itemVO = DietItemVO.fromEntity(item, matched);
                if (matched != null && matched.getCalorie() != null && item.getEatWeight() != null) {
                    BigDecimal factor = item.getEatWeight().divide(new BigDecimal("100"), 4, BigDecimal.ROUND_HALF_UP);
                    totalCal = totalCal.add(matched.getCalorie().multiply(factor));
                }
                itemVOs.add(itemVO);
            }
        }
        vo.setItems(itemVOs);
        vo.setTotalCalories(totalCal.setScale(1, BigDecimal.ROUND_HALF_UP));
        return vo;
    }

    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }
    public String getMealDate() { return mealDate; }
    public void setMealDate(String mealDate) { this.mealDate = mealDate; }
    public String getMealType() { return mealType; }
    public void setMealType(String mealType) { this.mealType = mealType; }
    public BigDecimal getTotalCalories() { return totalCalories; }
    public void setTotalCalories(BigDecimal totalCalories) { this.totalCalories = totalCalories; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public List<DietItemVO> getItems() { return items; }
    public void setItems(List<DietItemVO> items) { this.items = items; }
}
