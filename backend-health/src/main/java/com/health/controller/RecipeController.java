package com.health.controller;

import com.health.dto.ApiResponse;
import com.health.entity.Recipe;
import com.health.entity.RecipeIngredient;
import com.health.service.RecipeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/recipes")
public class RecipeController {

    @Autowired
    private RecipeService recipeService;

    @GetMapping
    public ResponseEntity<ApiResponse<List<Map<String, Object>>>> searchRecipes(
            @RequestParam(name = "keyword", required = false) String keyword) {
        List<Map<String, Object>> recipes = recipeService.searchRecipesWithIngredients(keyword);
        return ResponseEntity.ok(ApiResponse.success(recipes));
    }

    @GetMapping("/{recipeId}")
    public ResponseEntity<ApiResponse<Recipe>> getRecipeById(@PathVariable Integer recipeId) {
        Recipe recipe = recipeService.getRecipeById(recipeId);
        if (recipe == null) {
            return ResponseEntity.ok(ApiResponse.error("菜谱不存在"));
        }
        return ResponseEntity.ok(ApiResponse.success(recipe));
    }

    @GetMapping("/{recipeId}/ingredients")
    public ResponseEntity<ApiResponse<List<RecipeIngredient>>> getIngredients(
            @PathVariable Integer recipeId) {
        List<RecipeIngredient> ingredients = recipeService.getIngredientsByRecipeId(recipeId);
        return ResponseEntity.ok(ApiResponse.success(ingredients));
    }

    @GetMapping("/{recipeId}/detail")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getRecipeDetail(
            @PathVariable Integer recipeId,
            @RequestParam(name = "userId", required = false) Integer userId) {
        Map<String, Object> result = recipeService.getRecipeWithSubstitution(recipeId, userId);
        if (result.isEmpty()) {
            return ResponseEntity.ok(ApiResponse.error("菜谱不存在"));
        }
        return ResponseEntity.ok(ApiResponse.success(result));
    }

    @PostMapping
    public ResponseEntity<ApiResponse<Recipe>> createRecipe(
            @RequestBody Map<String, Object> body) {
        Recipe recipe = new Recipe();
        recipe.setRecipeName((String) body.get("recipeName"));
        recipe.setDescription((String) body.get("description"));
        recipe.setTags((String) body.get("tags"));
        
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> ingredientMaps = (List<Map<String, Object>>) body.get("ingredients");
        List<RecipeIngredient> ingredients = new java.util.ArrayList<RecipeIngredient>();
        for (Map<String, Object> map : ingredientMaps) {
            RecipeIngredient ingredient = new RecipeIngredient();
            ingredient.setIngredientName((String) map.get("ingredientName"));
            ingredient.setAmount(java.math.BigDecimal.valueOf((Double) map.get("amount")));
            ingredient.setUnit((String) map.get("unit"));
            ingredients.add(ingredient);
        }
        
        Recipe saved = recipeService.createRecipe(recipe, ingredients);
        return ResponseEntity.ok(ApiResponse.success(saved));
    }

    @PutMapping("/{recipeId}")
    public ResponseEntity<ApiResponse<Recipe>> updateRecipe(
            @PathVariable Integer recipeId,
            @RequestBody Map<String, Object> body) {
        Recipe recipe = new Recipe();
        recipe.setRecipeName((String) body.get("recipeName"));
        recipe.setDescription((String) body.get("description"));
        recipe.setTags((String) body.get("tags"));
        
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> ingredientMaps = (List<Map<String, Object>>) body.get("ingredients");
        List<RecipeIngredient> ingredients = new java.util.ArrayList<RecipeIngredient>();
        for (Map<String, Object> map : ingredientMaps) {
            RecipeIngredient ingredient = new RecipeIngredient();
            ingredient.setIngredientName((String) map.get("ingredientName"));
            ingredient.setAmount(java.math.BigDecimal.valueOf((Double) map.get("amount")));
            ingredient.setUnit((String) map.get("unit"));
            ingredients.add(ingredient);
        }
        
        Recipe updated = recipeService.updateRecipe(recipeId, recipe, ingredients);
        if (updated == null) {
            return ResponseEntity.ok(ApiResponse.error("菜谱不存在"));
        }
        return ResponseEntity.ok(ApiResponse.success(updated));
    }

    @DeleteMapping("/{recipeId}")
    public ResponseEntity<ApiResponse<Void>> deleteRecipe(@PathVariable Integer recipeId) {
        recipeService.deleteRecipe(recipeId);
        return ResponseEntity.ok(ApiResponse.success(null));
    }
}