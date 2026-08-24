package com.health.service;

import com.health.dto.FoodDTO;
import com.health.entity.Food;
import com.health.repository.FoodRepository;
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
 * FoodService 单元测试
 * 覆盖搜索、CRUD、批量查找、DTO 转换
 */
@DisplayName("食物服务测试")
class FoodServiceTest {

    @Mock
    private FoodRepository foodRepository;

    @InjectMocks
    private FoodService foodService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    private Food createFood(Integer id, String name, String category, int calorie) {
        Food food = new Food();
        food.setFoodId(id);
        food.setFoodName(name);
        food.setFoodCategory(category);
        food.setCalorie(BigDecimal.valueOf(calorie));
        food.setProtein(BigDecimal.valueOf(10));
        food.setFat(BigDecimal.valueOf(5));
        food.setCarb(BigDecimal.valueOf(20));
        food.setStatus("approved");
        return food;
    }

    // ========== 搜索测试 ==========

    @Test
    @DisplayName("关键词搜索 - 返回匹配结果")
    void searchFoods_WithKeyword() {
        List<Food> foods = Arrays.asList(createFood(1, "苹果(去皮,生)", "水果", 52));
        when(foodRepository.searchByName("苹果")).thenReturn(foods);

        List<FoodDTO> result = foodService.searchFoods("苹果");

        assertEquals(1, result.size());
        assertEquals("苹果(去皮,生)", result.get(0).getFoodName());
        assertEquals("水果", result.get(0).getFoodCategory());
    }

    @Test
    @DisplayName("空关键词 - 返回所有已审核食物")
    void searchFoods_EmptyKeyword() {
        List<Food> foods = Arrays.asList(
            createFood(1, "苹果", "水果", 52),
            createFood(2, "牛奶", "奶类", 54)
        );
        when(foodRepository.findAllApproved()).thenReturn(foods);

        List<FoodDTO> result = foodService.searchFoods(null);

        assertEquals(2, result.size());
        verify(foodRepository).findAllApproved();
    }

    @Test
    @DisplayName("空字符串关键词 - 返回所有已审核食物")
    void searchFoods_BlankKeyword() {
        when(foodRepository.findAllApproved()).thenReturn(Collections.emptyList());

        List<FoodDTO> result = foodService.searchFoods("  ");

        assertTrue(result.isEmpty());
        verify(foodRepository).findAllApproved();
    }

    // ========== 分类查询 ==========

    @Test
    @DisplayName("按分类查询食物")
    void getFoodsByCategory() {
        List<Food> foods = Arrays.asList(
            createFood(1, "苹果", "水果", 52),
            createFood(2, "香蕉", "水果", 89)
        );
        when(foodRepository.findByCategory("水果")).thenReturn(foods);

        List<FoodDTO> result = foodService.getFoodsByCategory("水果");

        assertEquals(2, result.size());
    }

    // ========== 按 ID 查询 ==========

    @Test
    @DisplayName("按 ID 查询食物 - 存在")
    void getFoodById_Found() {
        Food food = createFood(1, "苹果", "水果", 52);
        when(foodRepository.findById(1)).thenReturn(Optional.of(food));

        FoodDTO result = foodService.getFoodById(1);

        assertNotNull(result);
        assertEquals("苹果", result.getFoodName());
    }

    @Test
    @DisplayName("按 ID 查询食物 - 不存在返回 null")
    void getFoodById_NotFound() {
        when(foodRepository.findById(999)).thenReturn(Optional.empty());

        FoodDTO result = foodService.getFoodById(999);

        assertNull(result);
    }

    // ========== 食物审核 ==========

    @Test
    @DisplayName("添加食物 - 状态设为 pending")
    void addFood_SetsPending() {
        Food food = createFood(null, "新食物", "蔬菜", 30);
        when(foodRepository.save(any(Food.class))).thenAnswer(inv -> {
            Food saved = inv.getArgument(0);
            saved.setFoodId(100);
            return saved;
        });

        Food result = foodService.addFood(food);

        assertEquals("pending", result.getStatus());
        assertEquals(100, result.getFoodId());
    }

    @Test
    @DisplayName("审核通过 - 状态变为 approved")
    void approveFood_Success() {
        Food food = createFood(1, "待审核", "蔬菜", 30);
        food.setStatus("pending");
        when(foodRepository.findById(1)).thenReturn(Optional.of(food));
        when(foodRepository.save(any(Food.class))).thenReturn(food);

        Food result = foodService.approveFood(1);

        assertEquals("approved", result.getStatus());
    }

    @Test
    @DisplayName("审核通过 - 食物不存在抛异常")
    void approveFood_NotFound() {
        when(foodRepository.findById(999)).thenReturn(Optional.empty());

        assertThrows(RuntimeException.class, () -> foodService.approveFood(999));
    }

    @Test
    @DisplayName("拒绝食物 - 状态变为 rejected")
    void rejectFood_Success() {
        Food food = createFood(1, "待审核", "蔬菜", 30);
        food.setStatus("pending");
        when(foodRepository.findById(1)).thenReturn(Optional.of(food));
        when(foodRepository.save(any(Food.class))).thenReturn(food);

        Food result = foodService.rejectFood(1);

        assertEquals("rejected", result.getStatus());
    }

    @Test
    @DisplayName("删除食物 - 存在时正常删除")
    void deleteFood_Exists() {
        when(foodRepository.existsById(1)).thenReturn(true);

        assertDoesNotThrow(() -> foodService.deleteFood(1));
        verify(foodRepository).deleteById(1);
    }

    @Test
    @DisplayName("删除食物 - 不存在抛异常")
    void deleteFood_NotExists() {
        when(foodRepository.existsById(999)).thenReturn(false);

        assertThrows(RuntimeException.class, () -> foodService.deleteFood(999));
    }

    // ========== 批量查找 ==========

    @Test
    @DisplayName("批量查找 - 精确匹配优先")
    void batchLookup_ExactMatch() {
        Food food = createFood(1, "鸡蛋", "肉蛋类", 144);
        when(foodRepository.findByNameExact("鸡蛋")).thenReturn(Arrays.asList(food));

        Map<String, FoodDTO> result = foodService.batchLookup(Arrays.asList("鸡蛋"));

        assertTrue(result.containsKey("鸡蛋"));
        assertEquals("鸡蛋", result.get("鸡蛋").getFoodName());
    }

    @Test
    @DisplayName("批量查找 - 精确失败回退模糊搜索")
    void batchLookup_FallbackToFuzzy() {
        when(foodRepository.findByNameExact("鸡胸")).thenReturn(Collections.emptyList());
        Food food = createFood(2, "鸡胸肉(生)", "肉蛋类", 133);
        when(foodRepository.searchByName("鸡胸")).thenReturn(Arrays.asList(food));

        Map<String, FoodDTO> result = foodService.batchLookup(Arrays.asList("鸡胸"));

        assertTrue(result.containsKey("鸡胸"));
        assertEquals("鸡胸肉(生)", result.get("鸡胸").getFoodName());
    }

    @Test
    @DisplayName("批量查找 - 空名称跳过")
    void batchLookup_SkipEmpty() {
        Map<String, FoodDTO> result = foodService.batchLookup(Arrays.asList("", null, "  "));

        assertTrue(result.isEmpty());
    }

    // ========== 更新食物 ==========

    @Test
    @DisplayName("更新食物 - 部分字段更新")
    void updateFood_PartialUpdate() {
        Food existing = createFood(1, "旧名称", "蔬菜", 30);
        Food update = new Food();
        update.setFoodName("新名称");
        update.setCalorie(BigDecimal.valueOf(50));

        when(foodRepository.findById(1)).thenReturn(Optional.of(existing));
        when(foodRepository.save(any(Food.class))).thenReturn(existing);

        Food result = foodService.updateFood(1, update);

        assertEquals("新名称", result.getFoodName());
        assertEquals(BigDecimal.valueOf(50), result.getCalorie());
        assertEquals("蔬菜", result.getFoodCategory()); // 未更新的字段保持不变
    }
}
