package com.health.service;

import com.health.entity.Food;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import org.mockito.Mockito;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

/**
 * RecipeService 食材匹配逻辑单元测试
 * 测试 FOOD_ALIASES 同义词映射和 findBestFoodMatch 多级匹配
 * 
 * 使用 Mockito mock 避免对 Repository 的依赖，通过 doCallRealMethod 执行实际匹配逻辑
 */
@DisplayName("食谱食材匹配测试")
class RecipeServiceTest {

    private RecipeService recipeService;

    @BeforeEach
    void setUp() {
        // 使用 mock 跳过构造函数注入，但保留 findBestFoodMatch 的真实逻辑
        recipeService = Mockito.mock(RecipeService.class);
        Mockito.doCallRealMethod().when(recipeService).findBestFoodMatch(Mockito.anyString(), Mockito.anyList());
    }

    // ========== FOOD_ALIASES 同义词映射测试 ==========

    @Test
    @DisplayName("调味料同义词：姜片→姜")
    void testSeasoningAlias_Ginger() {
        List<Food> allFoods = Arrays.asList(createFood("姜", "蔬菜", 41, 1.3, 0.4, 9));
        Food result = recipeService.findBestFoodMatch("姜片", allFoods);
        assertNotNull(result, "姜片应该匹配到姜");
        assertEquals("姜", result.getFoodName());
    }

    @Test
    @DisplayName("调味料同义词：生抽→酱油")
    void testSeasoningAlias_SoySauce() {
        List<Food> allFoods = Arrays.asList(createFood("酱油", "调味料", 56, 8, 0.1, 5));
        Food result = recipeService.findBestFoodMatch("生抽", allFoods);
        assertNotNull(result, "生抽应该匹配到酱油");
        assertEquals("酱油", result.getFoodName());
    }

    @Test
    @DisplayName("调味料同义词：老抽→酱油")
    void testSeasoningAlias_DarkSoySauce() {
        List<Food> allFoods = Arrays.asList(createFood("酱油", "调味料", 56, 8, 0.1, 5));
        Food result = recipeService.findBestFoodMatch("老抽", allFoods);
        assertNotNull(result, "老抽应该匹配到酱油");
        assertEquals("酱油", result.getFoodName());
    }

    @Test
    @DisplayName("调味料同义词：冰糖→白砂糖")
    void testSeasoningAlias_RockSugar() {
        List<Food> allFoods = Arrays.asList(createFood("白砂糖", "调味料", 387, 0, 0, 100));
        Food result = recipeService.findBestFoodMatch("冰糖", allFoods);
        assertNotNull(result, "冰糖应该匹配到白砂糖");
        assertEquals("白砂糖", result.getFoodName());
    }

    @Test
    @DisplayName("调味料同义词：盐→食盐")
    void testSeasoningAlias_Salt() {
        List<Food> allFoods = Arrays.asList(createFood("食盐", "调味料", 0, 0, 0, 0));
        Food result = recipeService.findBestFoodMatch("盐", allFoods);
        assertNotNull(result, "盐应该匹配到食盐");
        assertEquals("食盐", result.getFoodName());
    }

    @Test
    @DisplayName("调味料同义词：料酒→黄酒")
    void testSeasoningAlias_CookingWine() {
        List<Food> allFoods = Arrays.asList(createFood("黄酒", "调味料", 66, 1.6, 0, 2));
        Food result = recipeService.findBestFoodMatch("料酒", allFoods);
        assertNotNull(result, "料酒应该匹配到黄酒");
        assertEquals("黄酒", result.getFoodName());
    }

    // ========== 肉类生重默认测试 ==========

    @Test
    @DisplayName("肉类生重默认：鸡胸肉→鸡胸肉(生)")
    void testMeatRawWeight_ChickenBreast() {
        List<Food> allFoods = Arrays.asList(createFood("鸡胸肉(生)", "肉蛋类", 133, 31, 1.2, 0));
        Food result = recipeService.findBestFoodMatch("鸡胸肉", allFoods);
        assertNotNull(result, "鸡胸肉应该默认取生重");
        assertEquals("鸡胸肉(生)", result.getFoodName());
    }

    @Test
    @DisplayName("肉类生重默认：五花肉→五花肉(生)")
    void testMeatRawWeight_PorkBelly() {
        List<Food> allFoods = Arrays.asList(createFood("五花肉(生)", "肉蛋类", 395, 13, 37, 0));
        Food result = recipeService.findBestFoodMatch("五花肉", allFoods);
        assertNotNull(result, "五花肉应该默认取生重");
        assertEquals("五花肉(生)", result.getFoodName());
    }

    @Test
    @DisplayName("肉类生重默认：瘦牛肉→瘦牛肉(生)")
    void testMeatRawWeight_LeanBeef() {
        List<Food> allFoods = Arrays.asList(createFood("瘦牛肉(生)", "肉蛋类", 125, 22, 3.5, 0));
        Food result = recipeService.findBestFoodMatch("瘦牛肉", allFoods);
        assertNotNull(result, "瘦牛肉应该默认取生重");
        assertEquals("瘦牛肉(生)", result.getFoodName());
    }

    @Test
    @DisplayName("肉类生重默认：排骨→猪小排(生)")
    void testMeatRawWeight_Ribs() {
        List<Food> allFoods = Arrays.asList(createFood("猪小排(生)", "肉蛋类", 264, 18, 21, 0));
        Food result = recipeService.findBestFoodMatch("排骨", allFoods);
        assertNotNull(result, "排骨应该默认取生重");
        assertEquals("猪小排(生)", result.getFoodName());
    }

    @Test
    @DisplayName("肉类生重默认：鸡腿→鸡腿(生)")
    void testMeatRawWeight_ChickenLeg() {
        List<Food> allFoods = Arrays.asList(createFood("鸡腿(生)", "肉蛋类", 181, 20, 11, 0));
        Food result = recipeService.findBestFoodMatch("鸡腿", allFoods);
        assertNotNull(result, "鸡腿应该默认取生重");
        assertEquals("鸡腿(生)", result.getFoodName());
    }

    // ========== 蔬菜同义词测试 ==========

    @Test
    @DisplayName("蔬菜同义词：番茄→番茄(生)")
    void testVeggieAlias_Tomato() {
        List<Food> allFoods = Arrays.asList(createFood("番茄(生)", "蔬菜", 18, 0.9, 0.2, 4));
        Food result = recipeService.findBestFoodMatch("番茄", allFoods);
        assertNotNull(result, "番茄应该匹配到番茄(生)");
        assertEquals("番茄(生)", result.getFoodName());
    }

    @Test
    @DisplayName("蔬菜同义词：土豆→土豆(生)")
    void testVeggieAlias_Potato() {
        List<Food> allFoods = Arrays.asList(createFood("土豆(生)", "主食", 77, 2, 0.1, 17));
        Food result = recipeService.findBestFoodMatch("土豆", allFoods);
        assertNotNull(result, "土豆应该匹配到土豆(生)");
    }

    // ========== 多级匹配测试 ==========

    @Test
    @DisplayName("去括号精确匹配：西兰花→西兰花(煮)")
    void testDeParenthesisMatch_Broccoli() {
        List<Food> allFoods = Arrays.asList(createFood("西兰花(煮)", "蔬菜", 36, 2.6, 0.4, 7));
        Food result = recipeService.findBestFoodMatch("西兰花", allFoods);
        assertNotNull(result, "去括号后应该能匹配西兰花");
        assertTrue(result.getFoodName().contains("西兰花"));
    }

    @Test
    @DisplayName("包含匹配：鸡蛋→鸡蛋(全,煮)")
    void testContainsMatch_Egg() {
        List<Food> allFoods = Arrays.asList(createFood("鸡蛋(全,煮)", "肉蛋类", 144, 13, 10, 1));
        Food result = recipeService.findBestFoodMatch("鸡蛋", allFoods);
        assertNotNull(result, "鸡蛋应该匹配到鸡蛋(全,煮)");
        assertTrue(result.getFoodName().contains("鸡蛋"));
    }

    @Test
    @DisplayName("无匹配时返回null")
    void testNoMatch_ReturnsNull() {
        List<Food> allFoods = Arrays.asList(createFood("苹果(去皮,生)", "水果", 52, 0.3, 0.2, 14));
        Food result = recipeService.findBestFoodMatch("完全不存在的食材", allFoods);
        assertNull(result, "不存在的食材应返回null");
    }

    @Test
    @DisplayName("空列表返回null")
    void testEmptyList_ReturnsNull() {
        Food result = recipeService.findBestFoodMatch("鸡蛋", Collections.emptyList());
        assertNull(result, "空列表应返回null");
    }

    // ========== 主食同义词测试 ==========

    @Test
    @DisplayName("主食同义词：米饭→米饭(熟)")
    void testStapleAlias_Rice() {
        List<Food> allFoods = Arrays.asList(createFood("米饭(熟)", "主食", 130, 2.5, 0.3, 28));
        Food result = recipeService.findBestFoodMatch("米饭", allFoods);
        assertNotNull(result, "米饭应该匹配到米饭(熟)");
        assertEquals("米饭(熟)", result.getFoodName());
    }

    @Test
    @DisplayName("主食同义词：面条→面条(熟)")
    void testStapleAlias_Noodle() {
        List<Food> allFoods = Arrays.asList(createFood("面条(熟)", "主食", 110, 3.3, 0.5, 24));
        Food result = recipeService.findBestFoodMatch("面条", allFoods);
        assertNotNull(result, "面条应该匹配到面条(熟)");
        assertEquals("面条(熟)", result.getFoodName());
    }

    @Test
    @DisplayName("综合匹配：多个食物中找正确项")
    void testMultipleFoods_FindCorrect() {
        List<Food> allFoods = Arrays.asList(
            createFood("米饭(熟)", "主食", 130, 2.5, 0.3, 28),
            createFood("面条(熟)", "主食", 110, 3.3, 0.5, 24),
            createFood("鸡胸肉(生)", "肉蛋类", 133, 31, 1.2, 0),
            createFood("酱油", "调味料", 56, 8, 0.1, 5)
        );
        Food result = recipeService.findBestFoodMatch("生抽", allFoods);
        assertNotNull(result);
        assertEquals("酱油", result.getFoodName());
    }

    // ========== 工具方法 ==========

    private Food createFood(String name, String category, int calorie, double protein, double fat, double carb) {
        Food food = new Food();
        food.setFoodId(1);
        food.setFoodName(name);
        food.setFoodCategory(category);
        food.setCalorie(java.math.BigDecimal.valueOf(calorie));
        food.setProtein(java.math.BigDecimal.valueOf(protein));
        food.setFat(java.math.BigDecimal.valueOf(fat));
        food.setCarb(java.math.BigDecimal.valueOf(carb));
        return food;
    }
}
