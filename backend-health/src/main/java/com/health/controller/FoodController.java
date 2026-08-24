package com.health.controller;

import com.health.dto.ApiResponse;
import com.health.dto.FoodDTO;
import com.health.entity.Food;
import com.health.service.FoodService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.Set;

@RestController
@RequestMapping("/api/food")
public class FoodController {

    private final FoodService foodService;

    public FoodController(FoodService foodService) {
        this.foodService = foodService;
    }

    @GetMapping("/search")
    public ResponseEntity<ApiResponse<List<FoodDTO>>> searchFoods(@RequestParam(name = "keyword", required = false) String keyword) {
        List<FoodDTO> foods = foodService.searchFoods(keyword);
        return ResponseEntity.ok(ApiResponse.success(foods));
    }

    @GetMapping("/list")
    public ResponseEntity<ApiResponse<List<FoodDTO>>> getAllFoods() {
        List<FoodDTO> foods = foodService.getAllApprovedFoods();
        return ResponseEntity.ok(ApiResponse.success(foods));
    }

    @GetMapping("/category/{category}")
    public ResponseEntity<ApiResponse<List<FoodDTO>>> getFoodsByCategory(@PathVariable(name = "category") String category) {
        List<FoodDTO> foods = foodService.getFoodsByCategory(category);
        return ResponseEntity.ok(ApiResponse.success(foods));
    }

    @GetMapping("/{foodId}")
    public ResponseEntity<ApiResponse<FoodDTO>> getFoodById(@PathVariable(name = "foodId") Integer foodId) {
        FoodDTO food = foodService.getFoodById(foodId);
        if (food == null) {
            return ResponseEntity.badRequest().body(ApiResponse.error("食物不存在"));
        }
        return ResponseEntity.ok(ApiResponse.success(food));
    }

    @PostMapping("/batch-lookup")
    public ResponseEntity<ApiResponse<Map<String, FoodDTO>>> batchLookup(@RequestBody Map<String, List<String>> request) {
        List<String> names = request.getOrDefault("names", new java.util.ArrayList<>());
        Map<String, FoodDTO> result = foodService.batchLookup(names);
        return ResponseEntity.ok(ApiResponse.success(result));
    }

    @PostMapping("/add")
    public ResponseEntity<ApiResponse<Food>> addFood(@RequestBody Food food) {
        Food saved = foodService.addFood(food);
        return ResponseEntity.ok(ApiResponse.success("食物已提交，等待管理员审核", saved));
    }

    @GetMapping("/pending")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResponse<List<FoodDTO>>> getPendingFoods() {
        List<FoodDTO> foods = foodService.getPendingFoods();
        return ResponseEntity.ok(ApiResponse.success(foods));
    }

    @PostMapping("/approve/{foodId}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResponse<Food>> approveFood(@PathVariable(name = "foodId") Integer foodId) {
        try {
            Food approved = foodService.approveFood(foodId);
            return ResponseEntity.ok(ApiResponse.success("食物已审核通过", approved));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }

    @PostMapping("/reject/{foodId}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResponse<Food>> rejectFood(@PathVariable(name = "foodId") Integer foodId) {
        try {
            Food rejected = foodService.rejectFood(foodId);
            return ResponseEntity.ok(ApiResponse.success("食物已拒绝", rejected));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }
}
