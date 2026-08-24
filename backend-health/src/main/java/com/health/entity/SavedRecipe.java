package com.health.entity;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "saved_recipe")
public class SavedRecipe {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "user_id", nullable = false)
    private Integer userId;

    @Column(name = "title", nullable = false)
    private String title;

    @Column(name = "ingredients", columnDefinition = "TEXT")
    private String ingredients;

    @Column(name = "steps", columnDefinition = "TEXT")
    private String steps;

    @Column(name = "nutrition_summary", columnDefinition = "TEXT")
    private String nutritionSummary;

    @Column(name = "persona_tag")
    private String personaTag;

    /** 收藏来源：system=系统菜谱，generated=AI生成 */
    @Column(name = "source")
    private String source;

    /** 来源系统菜谱ID（收藏系统菜谱时记录，用于取消收藏时精确删除；AI生成菜谱为空） */
    @Column(name = "original_recipe_id")
    private Integer originalRecipeId;

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();

    public SavedRecipe() {}

    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }
    public Integer getUserId() { return userId; }
    public void setUserId(Integer userId) { this.userId = userId; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getIngredients() { return ingredients; }
    public void setIngredients(String ingredients) { this.ingredients = ingredients; }
    public String getSteps() { return steps; }
    public void setSteps(String steps) { this.steps = steps; }
    public String getNutritionSummary() { return nutritionSummary; }
    public void setNutritionSummary(String nutritionSummary) { this.nutritionSummary = nutritionSummary; }
    public String getPersonaTag() { return personaTag; }
    public void setPersonaTag(String personaTag) { this.personaTag = personaTag; }
    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }
    public Integer getOriginalRecipeId() { return originalRecipeId; }
    public void setOriginalRecipeId(Integer originalRecipeId) { this.originalRecipeId = originalRecipeId; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
