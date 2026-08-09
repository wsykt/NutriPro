package com.health.controller;

import com.health.dto.FoodDTO;
import com.health.service.FoodService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.health.dto.ApiResponse;

import java.math.BigDecimal;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;

/**
 * FoodController 单元测试
 * 覆盖搜索、分类查询、详情、批量查找
 */
@DisplayName("食物控制器测试")
class FoodControllerTest {

    @Mock
    private FoodService foodService;

    @InjectMocks
    private FoodController foodController;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    private FoodDTO createFoodDTO(Integer id, String name, String category, int calorie) {
        FoodDTO dto = new FoodDTO();
        dto.setFoodId(id);
        dto.setFoodName(name);
        dto.setFoodCategory(category);
        dto.setCalorie(BigDecimal.valueOf(calorie));
        dto.setProtein(BigDecimal.valueOf(10));
        dto.setFat(BigDecimal.valueOf(5));
        dto.setCarb(BigDecimal.valueOf(20));
        return dto;
    }

    @Test
    @DisplayName("GET /api/food/search?keyword=苹果 - 搜索成功")
    void searchFoods_Success() {
        List<FoodDTO> foods = Arrays.asList(createFoodDTO(1, "苹果(去皮,生)", "水果", 52));
        when(foodService.searchFoods("苹果")).thenReturn(foods);

        ResponseEntity<ApiResponse<List<FoodDTO>>> response = foodController.searchFoods("苹果");

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals(1, response.getBody().getData().size());
        assertEquals("苹果(去皮,生)", response.getBody().getData().get(0).getFoodName());
    }

    @Test
    @DisplayName("GET /api/food/search - 无关键词返回全部")
    void searchFoods_NoKeyword() {
        List<FoodDTO> foods = Arrays.asList(
                createFoodDTO(1, "苹果", "水果", 52),
                createFoodDTO(2, "牛奶", "奶类", 54)
        );
        when(foodService.searchFoods(null)).thenReturn(foods);

        ResponseEntity<ApiResponse<List<FoodDTO>>> response = foodController.searchFoods(null);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals(2, response.getBody().getData().size());
    }

    @Test
    @DisplayName("GET /api/food/category/水果 - 分类查询")
    void getFoodsByCategory() {
        List<FoodDTO> foods = Arrays.asList(
                createFoodDTO(1, "苹果", "水果", 52),
                createFoodDTO(2, "香蕉", "水果", 89)
        );
        when(foodService.getFoodsByCategory("水果")).thenReturn(foods);

        ResponseEntity<ApiResponse<List<FoodDTO>>> response = foodController.getFoodsByCategory("水果");

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals(2, response.getBody().getData().size());
    }

    @Test
    @DisplayName("GET /api/food/1 - 按 ID 查询存在")
    void getFoodById_Found() {
        FoodDTO food = createFoodDTO(1, "苹果", "水果", 52);
        when(foodService.getFoodById(1)).thenReturn(food);

        ResponseEntity<ApiResponse<FoodDTO>> response = foodController.getFoodById(1);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals("苹果", response.getBody().getData().getFoodName());
    }

    @Test
    @DisplayName("GET /api/food/999 - 按 ID 查询不存在返回 400")
    void getFoodById_NotFound() {
        when(foodService.getFoodById(999)).thenReturn(null);

        ResponseEntity<ApiResponse<FoodDTO>> response = foodController.getFoodById(999);

        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        assertEquals("食物不存在", response.getBody().getMessage());
    }

    @Test
    @DisplayName("POST /api/food/batch-lookup - 批量查找")
    void batchLookup() {
        Map<String, FoodDTO> lookupResult = new HashMap<>();
        lookupResult.put("苹果", createFoodDTO(1, "苹果", "水果", 52));
        lookupResult.put("牛奶", createFoodDTO(2, "牛奶", "奶类", 54));
        when(foodService.batchLookup(anyList())).thenReturn(lookupResult);

        Map<String, List<String>> request = new HashMap<>();
        request.put("names", Arrays.asList("苹果", "牛奶"));

        ResponseEntity<ApiResponse<Map<String, FoodDTO>>> response = foodController.batchLookup(request);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertTrue(response.getBody().getData().containsKey("苹果"));
    }

    @Test
    @DisplayName("GET /api/food/list - 获取全部已审核食物")
    void getAllFoods() {
        List<FoodDTO> foods = Arrays.asList(
                createFoodDTO(1, "苹果", "水果", 52),
                createFoodDTO(2, "牛奶", "奶类", 54)
        );
        when(foodService.getAllApprovedFoods()).thenReturn(foods);

        ResponseEntity<ApiResponse<List<FoodDTO>>> response = foodController.getAllFoods();

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals(2, response.getBody().getData().size());
    }
}
