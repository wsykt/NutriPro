package com.health.service;

import com.health.dto.AddMealRequest;
import com.health.entity.DietItem;
import com.health.entity.DietMeal;
import com.health.entity.Food;
import com.health.entity.User;
import com.health.repository.DietItemRepository;
import com.health.repository.DietMealRepository;
import com.health.repository.FoodRepository;
import com.health.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import java.math.BigDecimal;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * DietService 单元测试
 * 覆盖添加/删除饮食记录、按日期查询、营养分析
 */
@DisplayName("膳食服务测试")
class DietServiceTest {

    @Mock
    private DietMealRepository dietMealRepository;
    @Mock
    private DietItemRepository dietItemRepository;
    @Mock
    private FoodRepository foodRepository;
    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private DietService dietService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    private Food createFood(Integer id, String name, double calorie, double protein, double fat, double carb) {
        Food food = new Food();
        food.setFoodId(id);
        food.setFoodName(name);
        food.setFoodCategory("测试");
        food.setCalorie(BigDecimal.valueOf(calorie));
        food.setProtein(BigDecimal.valueOf(protein));
        food.setFat(BigDecimal.valueOf(fat));
        food.setCarb(BigDecimal.valueOf(carb));
        food.setDietFiber(BigDecimal.valueOf(2));
        food.setCalcium(BigDecimal.valueOf(50));
        food.setDha(BigDecimal.valueOf(10));
        food.setFolicAcid(BigDecimal.valueOf(20));
        return food;
    }

    private User createUser(Integer id, String name, double weight, double height, int age, String gender, String crowdType) {
        User user = new User();
        user.setUserId(id);
        user.setUsername(name);
        user.setWeight(weight);
        user.setHeight(height);
        user.setAge(age);
        user.setGender(gender);
        user.setCrowdType(crowdType);
        return user;
    }

    // ========== 添加饮食记录 ==========

    @Test
    @DisplayName("添加饮食记录 - 成功保存")
    void addMeal_Success() {
        AddMealRequest request = new AddMealRequest();
        request.setEatDate("2026-07-26");
        request.setMealType("早餐");
        request.setRemark("测试早餐");

        AddMealRequest.MealItem item = new AddMealRequest.MealItem();
        item.setFoodId(1);
        item.setEatWeight(BigDecimal.valueOf(200));
        request.setItems(Arrays.asList(item));

        when(dietMealRepository.save(any(DietMeal.class))).thenAnswer(inv -> {
            DietMeal m = inv.getArgument(0);
            m.setMealId(100);
            return m;
        });

        DietMeal result = dietService.addMeal(1, request);

        assertNotNull(result);
        assertEquals(100, result.getMealId());
        assertEquals("早餐", result.getMealType());
        verify(dietMealRepository).save(any(DietMeal.class));
        verify(dietItemRepository).save(any(DietItem.class));
    }

    @Test
    @DisplayName("添加饮食记录 - 多个食物项")
    void addMeal_MultipleItems() {
        AddMealRequest request = new AddMealRequest();
        request.setEatDate("2026-07-26");
        request.setMealType("午餐");

        AddMealRequest.MealItem item1 = new AddMealRequest.MealItem();
        item1.setFoodId(1);
        item1.setEatWeight(BigDecimal.valueOf(200));
        AddMealRequest.MealItem item2 = new AddMealRequest.MealItem();
        item2.setFoodId(2);
        item2.setEatWeight(BigDecimal.valueOf(150));
        request.setItems(Arrays.asList(item1, item2));

        when(dietMealRepository.save(any(DietMeal.class))).thenAnswer(inv -> {
            DietMeal m = inv.getArgument(0);
            m.setMealId(101);
            return m;
        });

        DietMeal result = dietService.addMeal(1, request);

        verify(dietItemRepository, times(2)).save(any(DietItem.class));
    }

    // ========== 删除饮食记录 ==========

    @Test
    @DisplayName("删除饮食记录 - 本人操作成功")
    void deleteMeal_ByOwner() {
        DietMeal meal = new DietMeal();
        meal.setMealId(100);
        meal.setUserId(1);
        when(dietMealRepository.findById(100)).thenReturn(Optional.of(meal));
        when(dietItemRepository.findByMealId(100)).thenReturn(Collections.emptyList());

        boolean result = dietService.deleteMeal(1, 100);

        assertTrue(result);
        verify(dietMealRepository).delete(meal);
    }

    @Test
    @DisplayName("删除饮食记录 - 非本人操作返回 false")
    void deleteMeal_ByOtherUser() {
        DietMeal meal = new DietMeal();
        meal.setMealId(100);
        meal.setUserId(2);
        when(dietMealRepository.findById(100)).thenReturn(Optional.of(meal));

        boolean result = dietService.deleteMeal(1, 100);

        assertFalse(result);
        verify(dietMealRepository, never()).delete(any());
    }

    @Test
    @DisplayName("删除饮食记录 - 记录不存在返回 false")
    void deleteMeal_NotFound() {
        when(dietMealRepository.findById(999)).thenReturn(Optional.empty());

        boolean result = dietService.deleteMeal(1, 999);

        assertFalse(result);
    }

    @Test
    @DisplayName("删除饮食记录 - 级联删除子项")
    void deleteMeal_CascadeDeleteItems() {
        DietMeal meal = new DietMeal();
        meal.setMealId(100);
        meal.setUserId(1);
        List<DietItem> items = Arrays.asList(new DietItem(), new DietItem());
        when(dietMealRepository.findById(100)).thenReturn(Optional.of(meal));
        when(dietItemRepository.findByMealId(100)).thenReturn(items);

        boolean result = dietService.deleteMeal(1, 100);

        assertTrue(result);
        verify(dietItemRepository).deleteAll(items);
        verify(dietMealRepository).delete(meal);
    }

    // ========== 按日期查询 ==========

    @Test
    @DisplayName("按日期查询 - 返回完整饮食数据")
    void getMealsByDate_WithData() {
        DietMeal meal = new DietMeal();
        meal.setMealId(100);
        meal.setUserId(1);
        meal.setEatDate("2026-07-26");
        meal.setMealType("早餐");

        DietItem item = new DietItem();
        item.setItemId(1);
        item.setMealId(100);
        item.setFoodId(10);
        item.setEatWeight(BigDecimal.valueOf(200));

        Food food = createFood(10, "苹果", 52, 0.3, 0.2, 14);

        when(dietMealRepository.findByUserIdAndEatDate(1, "2026-07-26")).thenReturn(Arrays.asList(meal));
        when(dietItemRepository.findByMealIdIn(anyList())).thenReturn(Arrays.asList(item));
        when(foodRepository.findAllById(anyIterable())).thenReturn(Arrays.asList(food));

        List<Map<String, Object>> result = dietService.getMealsByDate(1, "2026-07-26");

        assertEquals(1, result.size());
        assertEquals("早餐", result.get(0).get("mealType"));
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> items = (List<Map<String, Object>>) result.get(0).get("items");
        assertEquals(1, items.size());
        assertEquals("苹果", items.get(0).get("foodName"));
    }

    @Test
    @DisplayName("按日期查询 - 无数据返回空列表")
    void getMealsByDate_Empty() {
        when(dietMealRepository.findByUserIdAndEatDate(1, "2026-01-01")).thenReturn(Collections.emptyList());

        List<Map<String, Object>> result = dietService.getMealsByDate(1, "2026-01-01");

        assertTrue(result.isEmpty());
    }

    // ========== 营养分析 ==========

    @Test
    @DisplayName("营养分析 - 正常计算")
    void analyzeDiet_Success() {
        User user = createUser(1, "测试", 70.0, 175.0, 30, "男", "普通人");
        when(userRepository.findById(1)).thenReturn(Optional.of(user));

        DietMeal meal = new DietMeal();
        meal.setMealId(100);
        meal.setUserId(1);
        meal.setEatDate("2026-07-26");
        meal.setMealType("早餐");

        DietItem item = new DietItem();
        item.setMealId(100);
        item.setFoodId(10);
        item.setEatWeight(BigDecimal.valueOf(200));

        Food food = createFood(10, "苹果", 52, 0.3, 0.2, 14);

        when(dietMealRepository.findByUserIdAndEatDate(1, "2026-07-26")).thenReturn(Arrays.asList(meal));
        when(dietItemRepository.findByMealIdIn(anyList())).thenReturn(Arrays.asList(item));
        when(foodRepository.findAllById(anyIterable())).thenReturn(Arrays.asList(food));

        Map<String, Object> result = dietService.analyzeDiet(1, "2026-07-26");

        assertNotNull(result);
        assertTrue(result.containsKey("user"));
        assertTrue(result.containsKey("total"));
        assertTrue(result.containsKey("recommendations"));
        assertTrue(result.containsKey("status"));
        assertTrue(result.containsKey("warnings"));
    }

    @Test
    @DisplayName("营养分析 - 用户不存在抛异常")
    void analyzeDiet_UserNotFound() {
        when(userRepository.findById(999)).thenReturn(Optional.empty());

        assertThrows(RuntimeException.class, () -> dietService.analyzeDiet(999, "2026-07-26"));
    }

    @Test
    @DisplayName("营养分析 - 无饮食记录返回零值")
    void analyzeDiet_NoMeals() {
        User user = createUser(1, "测试", 70.0, 175.0, 30, "男", "普通人");
        when(userRepository.findById(1)).thenReturn(Optional.of(user));
        when(dietMealRepository.findByUserIdAndEatDate(1, "2026-01-01")).thenReturn(Collections.emptyList());

        Map<String, Object> result = dietService.analyzeDiet(1, "2026-01-01");

        assertNotNull(result);
        @SuppressWarnings("unchecked")
        Map<String, Object> total = (Map<String, Object>) result.get("total");
        assertEquals(0, ((BigDecimal) total.get("calorie")).intValue());
    }
}
