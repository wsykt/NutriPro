package com.health.service;

import com.health.dto.FoodDTO;
import com.health.entity.Food;
import com.health.repository.FoodRepository;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.Caching;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.stream.Collectors;

import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
public class FoodService {

    private final FoodRepository foodRepository;

    public FoodService(FoodRepository foodRepository) {
        this.foodRepository = foodRepository;
    }

    @Cacheable(cacheNames = "foodSearch", key = "#keyword")
    public List<FoodDTO> searchFoods(String keyword) {
        log.info("开始搜索食物, keyword={}", keyword);
        List<Food> foods;
        if (keyword == null || keyword.trim().isEmpty()) {
            foods = foodRepository.findAllApproved();
        } else {
            foods = foodRepository.searchByName(keyword);
        }
        return foods.stream().map(this::toDTO).collect(Collectors.toList());
    }

    @Cacheable(cacheNames = "foodCategory", key = "#category")
    public List<FoodDTO> getFoodsByCategory(String category) {
        List<Food> foods = foodRepository.findByCategory(category);
        return foods.stream().map(this::toDTO).collect(Collectors.toList());
    }

    @Cacheable(cacheNames = "foodAllApproved")
    public List<FoodDTO> getAllApprovedFoods() {
        List<Food> foods = foodRepository.findAllApproved();
        return foods.stream().map(this::toDTO).collect(Collectors.toList());
    }

    @Cacheable(cacheNames = "foodById", key = "#foodId")
    public FoodDTO getFoodById(Integer foodId) {
        Food food = foodRepository.findById(foodId).orElse(null);
        return food != null ? toDTO(food) : null;
    }

    @Caching(evict = {
            @CacheEvict(cacheNames = "foodSearch", allEntries = true),
            @CacheEvict(cacheNames = "foodCategory", allEntries = true),
            @CacheEvict(cacheNames = "foodAllApproved", allEntries = true),
            @CacheEvict(cacheNames = "foodById", allEntries = true)
    })
    public Food addFood(Food food) {
        food.setStatus("pending");
        return foodRepository.save(food);
    }

    @Caching(evict = {
            @CacheEvict(cacheNames = "foodSearch", allEntries = true),
            @CacheEvict(cacheNames = "foodCategory", allEntries = true),
            @CacheEvict(cacheNames = "foodAllApproved", allEntries = true),
            @CacheEvict(cacheNames = "foodById", allEntries = true)
    })
    public Food approveFood(Integer foodId) {
        Food food = foodRepository.findById(foodId).orElseThrow(() -> new RuntimeException("食物不存在"));
        food.setStatus("approved");
        return foodRepository.save(food);
    }

    @Caching(evict = {
            @CacheEvict(cacheNames = "foodSearch", allEntries = true),
            @CacheEvict(cacheNames = "foodCategory", allEntries = true),
            @CacheEvict(cacheNames = "foodAllApproved", allEntries = true),
            @CacheEvict(cacheNames = "foodById", allEntries = true)
    })
    public Food rejectFood(Integer foodId) {
        Food food = foodRepository.findById(foodId).orElseThrow(() -> new RuntimeException("食物不存在"));
        food.setStatus("rejected");
        return foodRepository.save(food);
    }

    public List<FoodDTO> getPendingFoods() {
        List<Food> foods = foodRepository.findByStatus("pending");
        return foods.stream().map(this::toDTO).collect(Collectors.toList());
    }

    public List<Food> getAllFoods() {
        return foodRepository.findAll();
    }

    @Caching(evict = {
            @CacheEvict(cacheNames = "foodSearch", allEntries = true),
            @CacheEvict(cacheNames = "foodCategory", allEntries = true),
            @CacheEvict(cacheNames = "foodAllApproved", allEntries = true),
            @CacheEvict(cacheNames = "foodById", allEntries = true)
    })
    public Food updateFood(Integer foodId, Food updated) {
        Food food = foodRepository.findById(foodId).orElseThrow(() -> new RuntimeException("食物不存在"));
        if (updated.getFoodName() != null) food.setFoodName(updated.getFoodName());
        if (updated.getFoodCategory() != null) food.setFoodCategory(updated.getFoodCategory());
        if (updated.getCalorie() != null) food.setCalorie(updated.getCalorie());
        if (updated.getProtein() != null) food.setProtein(updated.getProtein());
        if (updated.getFat() != null) food.setFat(updated.getFat());
        if (updated.getCarb() != null) food.setCarb(updated.getCarb());
        if (updated.getDietFiber() != null) food.setDietFiber(updated.getDietFiber());
        if (updated.getGiValue() != null) food.setGiValue(updated.getGiValue());
        if (updated.getCalcium() != null) food.setCalcium(updated.getCalcium());
        if (updated.getDha() != null) food.setDha(updated.getDha());
        if (updated.getFolicAcid() != null) food.setFolicAcid(updated.getFolicAcid());
        if (updated.getStatus() != null) food.setStatus(updated.getStatus());
        return foodRepository.save(food);
    }

    @Caching(evict = {
            @CacheEvict(cacheNames = "foodSearch", allEntries = true),
            @CacheEvict(cacheNames = "foodCategory", allEntries = true),
            @CacheEvict(cacheNames = "foodAllApproved", allEntries = true),
            @CacheEvict(cacheNames = "foodById", allEntries = true)
    })
    public void deleteFood(Integer foodId) {
        if (!foodRepository.existsById(foodId)) throw new RuntimeException("食物不存在");
        foodRepository.deleteById(foodId);
    }

    private FoodDTO toDTO(Food food) {
        FoodDTO dto = new FoodDTO();
        dto.setFoodId(food.getFoodId());
        dto.setFoodName(food.getFoodName());
        dto.setFoodCategory(food.getFoodCategory());
        dto.setCalorie(food.getCalorie());
        dto.setProtein(food.getProtein());
        dto.setFat(food.getFat());
        dto.setCarb(food.getCarb());
        dto.setDietFiber(food.getDietFiber());
        dto.setGiValue(food.getGiValue());
        dto.setCalcium(food.getCalcium());
        dto.setDha(food.getDha());
        dto.setFolicAcid(food.getFolicAcid());
        return dto;
    }

    /**
     * 批量根据食材名称从数据库查找匹配的食材
     */
    public Map<String, FoodDTO> batchLookup(List<String> ingredientNames) {
        Map<String, FoodDTO> result = new HashMap<>();
        for (String name : ingredientNames) {
            if (name == null || name.trim().isEmpty()) continue;
            String trimmed = name.trim();
            // 先用精确匹配
            List<Food> exact = foodRepository.findByNameExact(trimmed);
            if (!exact.isEmpty()) {
                result.put(trimmed, toDTO(exact.get(0)));
                continue;
            }
            // 精确匹配失败则用模糊搜索
            List<Food> foods = foodRepository.searchByName(trimmed);
            if (!foods.isEmpty()) {
                result.put(trimmed, toDTO(foods.get(0)));
            }
        }
        return result;
    }
}
