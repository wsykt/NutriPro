package com.health.controller;

import com.health.dto.ApiResponse;
import com.health.entity.Recipe;
import com.health.entity.SavedRecipe;
import com.health.entity.User;
import com.health.repository.UserRepository;
import com.health.service.RecipeService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/recipe")
@CrossOrigin
public class RecipeUserController {

    private final UserRepository userRepository;
    private final RecipeService recipeService;

    public RecipeUserController(UserRepository userRepository, RecipeService recipeService) {
        this.userRepository = userRepository;
        this.recipeService = recipeService;
    }

    private User extractUser(Authentication authentication) {
        if (authentication == null) return null;
        if (authentication.getPrincipal() instanceof User) {
            return (User) authentication.getPrincipal();
        }
        try {
            return userRepository.findByUsername(authentication.getName()).orElse(null);
        } catch (Exception e) {
            return null;
        }
    }

    @GetMapping("/list")
    public ResponseEntity<ApiResponse<List<Recipe>>> listRecipes() {
        List<Recipe> recipes = recipeService.getAllRecipes();
        return ResponseEntity.ok(ApiResponse.success(recipes));
    }

    @GetMapping("/search")
    public ResponseEntity<ApiResponse<List<Recipe>>> searchRecipes(
            @RequestParam(required = false) String keyword) {
        List<Recipe> recipes = recipeService.searchRecipes(keyword);
        return ResponseEntity.ok(ApiResponse.success(recipes));
    }

    @GetMapping("/tag/{tag}")
    public ResponseEntity<ApiResponse<List<Recipe>>> getRecipesByTag(@PathVariable String tag) {
        List<Recipe> recipes = recipeService.getRecipesByTag(tag);
        return ResponseEntity.ok(ApiResponse.success(recipes));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Recipe>> getRecipe(@PathVariable Integer id) {
        Recipe recipe = recipeService.getRecipeById(id);
        if (recipe == null) {
            return ResponseEntity.ok(ApiResponse.error("菜谱不存在"));
        }
        return ResponseEntity.ok(ApiResponse.success(recipe));
    }

    @GetMapping("/tags")
    public ResponseEntity<ApiResponse<List<String>>> getTags() {
        List<String> tags = Arrays.asList("孕妇", "糖尿病", "老年人", "青少年", "高血压", "减脂", "健身", "低GI", "高蛋白", "均衡");
        return ResponseEntity.ok(ApiResponse.success(tags));
    }

    @GetMapping("/my-saved")
    public ResponseEntity<ApiResponse<List<SavedRecipe>>> getMySavedRecipes(Authentication authentication) {
        User user = extractUser(authentication);
        if (user == null || user.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }
        List<SavedRecipe> saved = recipeService.getSavedRecipes(user.getUserId());
        return ResponseEntity.ok(ApiResponse.success(saved));
    }

    @PostMapping("/save")
    public ResponseEntity<ApiResponse<SavedRecipe>> saveRecipe(
            Authentication authentication,
            @RequestBody Map<String, Object> body) {
        User user = extractUser(authentication);
        if (user == null || user.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }
        SavedRecipe saved = recipeService.saveUserRecipe(user.getUserId(), body);
        return ResponseEntity.ok(ApiResponse.success("保存成功", saved));
    }

    @DeleteMapping("/my-saved/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteSavedRecipe(
            Authentication authentication,
            @PathVariable Integer id) {
        User user = extractUser(authentication);
        if (user == null || user.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }
        recipeService.deleteSavedRecipe(user.getUserId(), id);
        return ResponseEntity.ok(ApiResponse.success("已删除", null));
    }
}
