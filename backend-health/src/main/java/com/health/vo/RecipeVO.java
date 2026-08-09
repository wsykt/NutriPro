package com.health.vo;

import com.health.entity.Recipe;
import com.health.entity.RecipeIngredient;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public class RecipeVO {

    private Integer id;
    private String name;
    private String description;
    private BigDecimal calories;
    private BigDecimal protein;
    private BigDecimal carbs;
    private BigDecimal fat;
    private BigDecimal fiber;
    private BigDecimal giValue;
    private BigDecimal calcium;
    private BigDecimal folicAcid;
    private BigDecimal dha;
    private String healthTags;
    private String category;
    private Integer cookingTimeMinutes;
    private Integer servings;
    private String imageUrl;
    private List<RecipeIngredientVO> ingredients;
    private Map<String, BigDecimal> nutrientPer100g;

    public RecipeVO() {}

    public static RecipeVO fromEntity(Recipe recipe) {
        return fromEntity(recipe, null);
    }

    public static RecipeVO fromEntity(Recipe recipe, List<RecipeIngredient> ingredients) {
        if (recipe == null) return null;
        RecipeVO vo = new RecipeVO();
        vo.setId(recipe.getRecipeId());
        vo.setName(recipe.getRecipeName());
        vo.setDescription(recipe.getDescription());
        vo.setCalories(recipe.getCalories());
        vo.setProtein(recipe.getProtein());
        vo.setCarbs(recipe.getCarbs());
        vo.setFat(recipe.getFat());
        vo.setFiber(recipe.getFiber());
        vo.setHealthTags(recipe.getTags());
        vo.setImageUrl(recipe.getCoverImageUrl());

        if (ingredients != null) {
            vo.setIngredients(ingredients.stream()
                    .map(RecipeIngredientVO::fromEntity)
                    .collect(Collectors.toList()));
        }

        Map<String, BigDecimal> per100g = new LinkedHashMap<>();
        per100g.put("calories", recipe.getCalories());
        per100g.put("protein", recipe.getProtein());
        per100g.put("fat", recipe.getFat());
        per100g.put("carbs", recipe.getCarbs());
        per100g.put("fiber", recipe.getFiber());
        vo.setNutrientPer100g(per100g);

        return vo;
    }

    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public BigDecimal getCalories() { return calories; }
    public void setCalories(BigDecimal calories) { this.calories = calories; }
    public BigDecimal getProtein() { return protein; }
    public void setProtein(BigDecimal protein) { this.protein = protein; }
    public BigDecimal getCarbs() { return carbs; }
    public void setCarbs(BigDecimal carbs) { this.carbs = carbs; }
    public BigDecimal getFat() { return fat; }
    public void setFat(BigDecimal fat) { this.fat = fat; }
    public BigDecimal getFiber() { return fiber; }
    public void setFiber(BigDecimal fiber) { this.fiber = fiber; }
    public BigDecimal getGiValue() { return giValue; }
    public void setGiValue(BigDecimal giValue) { this.giValue = giValue; }
    public BigDecimal getCalcium() { return calcium; }
    public void setCalcium(BigDecimal calcium) { this.calcium = calcium; }
    public BigDecimal getFolicAcid() { return folicAcid; }
    public void setFolicAcid(BigDecimal folicAcid) { this.folicAcid = folicAcid; }
    public BigDecimal getDha() { return dha; }
    public void setDha(BigDecimal dha) { this.dha = dha; }
    public String getHealthTags() { return healthTags; }
    public void setHealthTags(String healthTags) { this.healthTags = healthTags; }
    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }
    public Integer getCookingTimeMinutes() { return cookingTimeMinutes; }
    public void setCookingTimeMinutes(Integer cookingTimeMinutes) { this.cookingTimeMinutes = cookingTimeMinutes; }
    public Integer getServings() { return servings; }
    public void setServings(Integer servings) { this.servings = servings; }
    public String getImageUrl() { return imageUrl; }
    public void setImageUrl(String imageUrl) { this.imageUrl = imageUrl; }
    public List<RecipeIngredientVO> getIngredients() { return ingredients; }
    public void setIngredients(List<RecipeIngredientVO> ingredients) { this.ingredients = ingredients; }
    public Map<String, BigDecimal> getNutrientPer100g() { return nutrientPer100g; }
    public void setNutrientPer100g(Map<String, BigDecimal> nutrientPer100g) { this.nutrientPer100g = nutrientPer100g; }
}
