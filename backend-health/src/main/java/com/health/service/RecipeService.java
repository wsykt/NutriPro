package com.health.service;

import com.health.entity.Food;
import com.health.entity.Recipe;
import com.health.entity.RecipeIngredient;
import com.health.entity.User;
import com.health.repository.FoodRepository;
import com.health.repository.RecipeIngredientRepository;
import com.health.repository.RecipeRepository;
import com.health.repository.UserRepository;
import com.health.entity.SavedRecipe;
import com.health.repository.SavedRecipeRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.Caching;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.*;
import java.util.stream.Collectors;

import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
public class RecipeService {

    @Autowired
    private RecipeRepository recipeRepository;

    @Autowired
    private RecipeIngredientRepository recipeIngredientRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private SavedRecipeRepository savedRecipeRepository;

    @Autowired
    private FoodRepository foodRepository;

    private static final double HIGH_FAT_THRESHOLD = 20.0; // 每100g含脂肪>20g视为高脂
    private static final double HIGH_GI_THRESHOLD = 70.0;   // GI>70视为高GI
    private static final double HIGH_CALORIE_THRESHOLD = 250.0; // 每100g热量>250kcal视为高热量

    // ========== 食材同义词映射表（食谱名 → 食物库标准名） ==========

    /** 食谱食材名 → 食物库标准名 映射 */
    private static final Map<String, String> FOOD_ALIASES = new HashMap<String, String>() {{
        // 调味料/加工品 → 基础食材
        put("姜片", "姜");
        put("生姜", "姜");
        put("葱段", "葱");
        put("大葱", "葱");
        put("小葱", "葱");
        put("葱花", "葱");
        put("蒜", "大蒜");
        put("大蒜头", "大蒜");
        put("蒜末", "大蒜");
        put("生抽", "酱油");
        put("老抽", "酱油");
        put("蒸鱼豉油", "酱油");
        put("味极鲜", "酱油");
        put("料酒", "黄酒");
        put("冰糖", "白砂糖");
        put("白糖", "白砂糖");
        put("红糖", "白砂糖");
        put("盐", "食盐");
        put("鸡精", "食盐");
        put("味精", "食盐");
        put("醋", "香醋");
        put("陈醋", "香醋");
        put("白醋", "香醋");
        put("淀粉", "玉米淀粉");
        put("生粉", "玉米淀粉");
        put("香油", "芝麻油");
        put("麻油", "芝麻油");

        // 肉蛋类简称 → 标准名
        put("排骨", "猪小排(生)");
        put("小排", "猪小排(生)");
        put("大排", "猪大排(生)");
        put("牛腩", "牛腩(生)");
        put("牛腱", "牛腱子(生)");
        put("牛里脊", "瘦牛肉(生)");
        put("猪肉(瘦)", "瘦猪肉(生)");
        put("里脊肉", "瘦猪肉(生)");
        put("猪里脊", "瘦猪肉(生)");
        put("瘦肉", "瘦猪肉(生)");
        put("鸡腿", "鸡腿(生)");
        put("鸡腿肉", "鸡腿(生)");
        put("去骨鸡腿", "鸡腿(生)");
        put("鹌鹑蛋", "鹌鹑蛋(水煮)");
        put("鸭蛋", "鸭蛋(水煮)");
        put("猪油", "猪油(熬)");
        put("黄油", "黄油(无盐)");

        // 水产简称
        put("虾", "虾仁(生)");
        put("鲜虾", "虾仁(生)");
        put("大明虾", "虾仁(生)");
        put("三文鱼", "三文鱼(生)");
        put("鳕鱼", "鳕鱼(生)");
        put("鲈鱼", "鲈鱼(生)");
        put("带鱼", "带鱼(生)");
        put("鱿鱼", "鱿鱼(鲜生)");
        put("扇贝", "扇贝(鲜,生)");

        // 蔬菜别名
        put("番茄", "番茄(生)");
        put("西红柿", "番茄(生)");
        put("土豆", "土豆(生)");
        put("马铃薯", "土豆(生)");
        put("红薯", "红薯(蒸熟)");
        put("地瓜", "红薯(蒸熟)");
        put("玉米", "玉米(煮熟)");
        put("南瓜", "南瓜(生)");
        put("山药", "山药(生)");
        put("芋头", "芋头(生)");
        put("茄子", "茄子(生)");
        put("苦瓜", "苦瓜(生)");
        put("韭菜", "韭菜(生)");
        put("芹菜", "芹菜(生茎)");
        put("平菇", "平菇(生)");
        put("香菇", "香菇(生)");
        put("金针菇", "金针菇(生)");
        put("娃娃菜", "娃娃菜(生)");
        put("大白菜", "大白菜(生)");

        // 水果别名
        put("苹果", "苹果(去皮,生)");
        put("香蕉", "香蕉(生)");
        put("橙子", "橙子(生)");
        put("橘子", "橙子(生)");
        put("草莓", "草莓(生)");
        put("葡萄", "葡萄(生)");
        put("猕猴桃", "猕猴桃(生)");
        put("奇异果", "猕猴桃(生)");
        put("梨", "梨(生)");
        put("桃子", "桃子(生)");

        // 豆制品
        put("豆腐", "嫩豆腐");
        put("老豆腐", "嫩豆腐");
        put("豆腐皮", "豆腐皮(干生)");
        put("黄豆", "黄豆(生)");
        put("黑豆", "黑豆(生)");
        put("豆浆", "纯豆浆");

        // 主食别名
        put("米饭", "米饭(熟)");
        put("白米饭", "米饭(熟)");
        put("大米饭", "米饭(熟)");
        put("面条", "面条(熟)");
        put("挂面", "面条(生)");
        put("白面", "面粉(标准粉)");
        put("面粉", "面粉(标准粉)");
        put("小米", "小米(生)");
        put("燕麦", "燕麦片(干生纯燕麦)");
        put("糙米", "糙米(生)");
        put("荞麦面", "荞麦面(干生)");

        // 肉类生重默认（食谱食材默认取生重）
        put("鸡胸肉", "鸡胸肉(生)");
        put("五花肉", "五花肉(生)");
        put("瘦牛肉", "瘦牛肉(生)");
        put("瘦羊肉", "瘦羊肉(生)");
        put("瘦猪肉", "瘦猪肉(生)");
        put("牛里脊", "瘦牛肉(生)");

        // 通用食材别名
        put("食用油", "花生油");
        put("蒜蓉", "大蒜");
        put("花生米", "花生仁(生)");
        put("猪肝", "猪肝(生)");
        put("牛腱子", "牛腱子(生)");
        put("胡萝卜", "胡萝卜(生)");
        put("冬瓜", "冬瓜(生)");
        put("黄瓜", "黄瓜(生)");
        put("生菜", "生菜(生)");
        put("木耳", "木耳(干)");
        put("排骨", "猪小排(生)");
        put("脱脂牛奶", "脱脂牛奶");
    }};

    // ========== 智能替换规则引擎（参考 Demo substituteRules.ts） ==========

    /** 过敏原 → 匹配关键词映射 */
    private static final Map<String, List<String>> ALLERGEN_MATCH_TAGS = new HashMap<String, List<String>>() {{
        put("花生", Arrays.asList("花生", "花生米", "花生酱"));
        put("海鲜", Arrays.asList("虾", "虾仁", "蟹", "鱼", "鲈鱼", "带鱼", "鱿鱼", "扇贝", "贝壳", "水产"));
        put("鸡蛋", Arrays.asList("鸡蛋", "鸭蛋", "鹌鹑蛋"));
        put("大豆", Arrays.asList("豆腐", "豆制品", "黄豆", "豆浆", "豆皮", "豆瓣酱"));
        put("牛奶", Arrays.asList("牛奶", "乳制品", "酸奶", "奶酪", "黄油", "奶油"));
        put("小麦", Arrays.asList("面粉", "面食", "小麦", "面包", "馒头", "面条", "饺子皮"));
        put("坚果", Arrays.asList("坚果", "核桃", "杏仁", "腰果", "花生米", "松子"));
    }};

    /** 替换规则：restrictionType × 食材匹配模式 */
    private static final List<Map<String, Object>> SUBSTITUTION_RULES = new ArrayList<Map<String, Object>>() {{
        // 低脂规则
        add(ruleEntry("低脂", Arrays.asList("油腻", "高脂", "肥肉", "五花肉", "猪油", "黄油"), "高脂食材，不适合低脂饮食",
            Arrays.asList(
                altEntry("瘦肉", "减少60%脂肪"),
                altEntry("鸡胸肉", "低脂高蛋白(脂肪减少70%)"),
                altEntry("里脊肉", "低脂部位替代")
            )));
        add(ruleEntry("低脂", Arrays.asList("花生油", "大豆油", "葵花籽油"), "高脂食用油，不适合低脂饮食",
            Arrays.asList(
                altEntry("橄榄油", "优质不饱和脂肪酸"),
                altEntry("玉米油", "低脂替代")
            )));
        // 低盐规则
        add(ruleEntry("低盐", Arrays.asList("酱油", "老抽", "生抽", "盐", "咸菜", "咸鱼", "豆瓣酱"), "高盐食材，不适合低盐饮食",
            Arrays.asList(
                altEntry("低钠酱油(减半)", "减少50%钠摄入"),
                altEntry("柠檬汁", "无盐提味"),
                altEntry("薄盐生抽", "减盐30%")
            )));
        // 低糖规则
        add(ruleEntry("低糖", Arrays.asList("冰糖", "白糖", "红糖", "糖", "蜂蜜", "甜面酱"), "高糖食材，不适合低糖饮食",
            Arrays.asList(
                altEntry("赤藓糖醇(等量)", "零升糖替代"),
                altEntry("木糖醇(等量)", "低升糖替代"),
                altEntry("少量蜂蜜(1/3)", "减少用量")
            )));
        // 糖尿病规则
        add(ruleEntry("糖尿病", Arrays.asList("冰糖", "白糖", "红糖", "糖", "蜂蜜", "米饭", "面条", "白粥"), "高升糖食材，不适合糖尿病",
            Arrays.asList(
                altEntry("赤藓糖醇", "不影响血糖"),
                altEntry("杂粮饭", "低GI替代"),
                altEntry("荞麦面", "低GI主食替代")
            )));
        // 清淡/无辣规则
        add(ruleEntry("清淡", Arrays.asList("辣椒", "干辣椒", "花椒", "麻辣", "辣", "郫县豆瓣酱"), "辛辣食材，不适合清淡口味",
            Arrays.asList(
                altEntry("青椒", "不辣且富含维C"),
                altEntry("彩椒", "不辣富含维C"),
                altEntry("甜椒", "不辣替代")
            )));
    }};

    @SuppressWarnings("unchecked")
    private static Map<String, Object> ruleEntry(String restriction, List<String> keywords, String reason, List<Map<String, String>> alternatives) {
        Map<String, Object> entry = new HashMap<String, Object>();
        entry.put("restriction", restriction);
        entry.put("keywords", keywords);
        entry.put("reason", reason);
        entry.put("alternatives", alternatives);
        return entry;
    }

    private static Map<String, String> altEntry(String name, String benefit) {
        Map<String, String> alt = new HashMap<String, String>();
        alt.put("name", name);
        alt.put("benefit", benefit);
        return alt;
    }

    /** 基础替换规则（食材名→替代列表，兼容旧逻辑） */
    private Map<String, List<String>> substitutionRules = new HashMap<String, List<String>>() {{
        put("五花肉", Arrays.asList("瘦猪肉", "鸡胸肉", "瘦牛肉"));
        put("猪肉", Arrays.asList("瘦牛肉", "鸡胸肉", "鱼肉"));
        put("牛肉", Arrays.asList("瘦猪肉", "鸡胸肉", "鱼肉"));
        put("羊肉", Arrays.asList("瘦牛肉", "鸡胸肉", "鱼肉"));
        put("肥肉", Arrays.asList("瘦肉", "鸡胸肉", "鱼肉"));
        put("花生油", Arrays.asList("橄榄油", "玉米油", "菜籽油"));
        put("辣椒", Arrays.asList("青椒", "彩椒", "甜椒"));
        put("虾仁", Arrays.asList("龙利鱼", "鳕鱼", "鸡胸肉"));
        put("鸡蛋", Arrays.asList("鸭蛋", "鹌鹑蛋", "豆腐"));
        put("糖", Arrays.asList("赤藓糖醇", "木糖醇", "椰枣"));
    }};

    @Cacheable(cacheNames = "recipeSearch", key = "#keyword")
    public List<Recipe> searchRecipes(String keyword) {
        if (keyword == null || keyword.trim().isEmpty()) {
            return recipeRepository.findAll();
        }
        return recipeRepository.findByRecipeNameContainingOrTagsContaining(keyword, keyword);
    }

    /**
     * 获取所有食谱及其食材（前端列表用）
     */
    public List<Map<String, Object>> getAllRecipesWithIngredients() {
        List<Recipe> recipes = recipeRepository.findAll();
        List<Map<String, Object>> result = new ArrayList<Map<String, Object>>();
        for (Recipe r : recipes) {
            Map<String, Object> map = new HashMap<String, Object>();
            map.put("recipeId", r.getRecipeId());
            map.put("recipeName", r.getRecipeName());
            map.put("description", r.getDescription());
            map.put("calories", r.getCalories());
            map.put("protein", r.getProtein());
            map.put("fat", r.getFat());
            map.put("carbs", r.getCarbs());
            map.put("fiber", r.getFiber());
            map.put("tags", r.getTags());
            map.put("source", r.getSource());
            map.put("calories", r.getCalories());
            map.put("ingredients", getIngredientsByRecipeId(r.getRecipeId()));
            result.add(map);
        }
        return result;
    }

    public List<Map<String, Object>> searchRecipesWithIngredients(String keyword) {
        List<Recipe> recipes;
        if (keyword == null || keyword.trim().isEmpty()) {
            recipes = recipeRepository.findAll();
        } else {
            recipes = recipeRepository.findByRecipeNameContainingOrTagsContaining(keyword, keyword);
        }
        List<Map<String, Object>> result = new ArrayList<Map<String, Object>>();
        for (Recipe r : recipes) {
            Map<String, Object> map = new HashMap<String, Object>();
            map.put("recipeId", r.getRecipeId());
            map.put("recipeName", r.getRecipeName());
            map.put("description", r.getDescription());
            map.put("calories", r.getCalories());
            map.put("protein", r.getProtein());
            map.put("fat", r.getFat());
            map.put("carbs", r.getCarbs());
            map.put("fiber", r.getFiber());
            map.put("tags", r.getTags());
            map.put("source", r.getSource());
            map.put("ingredients", getIngredientsByRecipeId(r.getRecipeId()));
            result.add(map);
        }
        return result;
    }

    @Cacheable(cacheNames = "recipeById", key = "#recipeId")
    public Recipe getRecipeById(Integer recipeId) {
        return recipeRepository.findById(recipeId).orElse(null);
    }

    public List<RecipeIngredient> getIngredientsByRecipeId(Integer recipeId) {
        return recipeIngredientRepository.findByRecipeId(recipeId);
    }

    @Caching(evict = {
            @CacheEvict(cacheNames = "recipeSearch", allEntries = true),
            @CacheEvict(cacheNames = "recipeById", allEntries = true),
            @CacheEvict(cacheNames = "recipeByTag", allEntries = true)
    })
    @Transactional
    public Recipe createRecipe(Recipe recipe, List<RecipeIngredient> ingredients) {
        Recipe savedRecipe = recipeRepository.save(recipe);
        for (RecipeIngredient ingredient : ingredients) {
            ingredient.setRecipeId(savedRecipe.getRecipeId());
        }
        recipeIngredientRepository.saveAll(ingredients);
        return savedRecipe;
    }

    @Caching(evict = {
            @CacheEvict(cacheNames = "recipeSearch", allEntries = true),
            @CacheEvict(cacheNames = "recipeById", allEntries = true),
            @CacheEvict(cacheNames = "recipeByTag", allEntries = true)
    })
    @Transactional
    public Recipe updateRecipe(Integer recipeId, Recipe recipe, List<RecipeIngredient> ingredients) {
        Recipe existingRecipe = recipeRepository.findById(recipeId).orElse(null);
        if (existingRecipe == null) {
            return null;
        }
        existingRecipe.setRecipeName(recipe.getRecipeName());
        existingRecipe.setDescription(recipe.getDescription());
        existingRecipe.setCalories(recipe.getCalories());
        existingRecipe.setProtein(recipe.getProtein());
        existingRecipe.setFat(recipe.getFat());
        existingRecipe.setCarbs(recipe.getCarbs());
        existingRecipe.setFiber(recipe.getFiber());
        existingRecipe.setTags(recipe.getTags());
        recipeRepository.save(existingRecipe);
        recipeIngredientRepository.deleteByRecipeId(recipeId);
        for (RecipeIngredient ingredient : ingredients) {
            ingredient.setRecipeId(recipeId);
        }
        recipeIngredientRepository.saveAll(ingredients);
        return existingRecipe;
    }

    @Caching(evict = {
            @CacheEvict(cacheNames = "recipeSearch", allEntries = true),
            @CacheEvict(cacheNames = "recipeById", allEntries = true),
            @CacheEvict(cacheNames = "recipeByTag", allEntries = true)
    })
    @Transactional
    public void deleteRecipe(Integer recipeId) {
        recipeIngredientRepository.deleteByRecipeId(recipeId);
        recipeRepository.deleteById(recipeId);
    }

    public Map<String, Object> getRecipeWithSubstitution(Integer recipeId, Integer userId) {
        log.info("开始智能食谱替换分析, recipeId={}, userId={}", recipeId, userId);
        Map<String, Object> result = new HashMap<String, Object>();
        Recipe recipe = getRecipeById(recipeId);
        if (recipe == null) {
            return result;
        }
        result.put("recipe", recipe);
        
        List<RecipeIngredient> ingredients = getIngredientsByRecipeId(recipeId);
        result.put("ingredients", ingredients);
        
        User user = userId != null ? userRepository.findById(userId).orElse(null) : null;
        // 规则基替换（过敏/口味/饮食限制）
        List<Map<String, Object>> substitutions = analyzeIngredients(ingredients, user);
        result.put("substitutions", substitutions);
        // 食物数据库基替换（高脂/高GI/高热量 -> 同类别更优食材）
        List<Map<String, Object>> foodDbSubstitutions = analyzeIngredientsWithFoodDB(ingredients);
        result.put("foodDbSubstitutions", foodDbSubstitutions);
        
        // 添加食材营养估算（用于前端营养变化对比）
        List<Map<String, Object>> ingredientNutrition = estimateIngredientNutrition(ingredients);
        result.put("ingredientNutrition", ingredientNutrition);

        // 聚合整份菜谱的 DHA、叶酸总和以及加权平均 GI
        double totalFolicAcid = 0;
        double totalDha = 0;
        double totalGi = 0;
        for (Map<String, Object> n : ingredientNutrition) {
            if (n.containsKey("folicAcid")) {
                totalFolicAcid += ((Number) n.get("folicAcid")).doubleValue();
            }
            if (n.containsKey("dha")) {
                totalDha += ((Number) n.get("dha")).doubleValue();
            }
            if (n.containsKey("giContribution")) {
                totalGi += ((Number) n.get("giContribution")).doubleValue();
            }
        }
        Map<String, Object> aggregatedNutrition = new HashMap<String, Object>();
        aggregatedNutrition.put("folicAcid", Math.round(totalFolicAcid * 100) / 100.0);
        aggregatedNutrition.put("dha", Math.round(totalDha * 100) / 100.0);
        aggregatedNutrition.put("gi", Math.round(totalGi * 10) / 10.0);
        result.put("aggregatedNutrition", aggregatedNutrition);
        
        // 添加替换后预估营养变化
        Map<String, Object> nutritionChange = calculatePotentialNutritionChange(substitutions, foodDbSubstitutions, ingredientNutrition);
        result.put("nutritionChange", nutritionChange);
        
        log.info("智能食谱替换分析完成, recipeId={}, userId={}", recipeId, userId);
        return result;
    }

    /**
     * 估算每种食材的营养值（基于食物数据库匹配）
     * 仅聚合 show_gi/show_folic_acid/show_dha 为 1 的字段；
     * GI 值按各食材摄入量加权平均，DHA/叶酸按摄入量累加
     */
    private List<Map<String, Object>> estimateIngredientNutrition(List<RecipeIngredient> ingredients) {
        List<Map<String, Object>> result = new ArrayList<Map<String, Object>>();
        List<Food> allFoods = foodRepository.findAll();

        double totalWeight = 0;
        for (RecipeIngredient ing : ingredients) {
            if (ing.getAmount() != null && ing.getUnit() != null && "g".equals(ing.getUnit())) {
                totalWeight += ing.getAmount().doubleValue();
            }
        }

        for (RecipeIngredient ing : ingredients) {
            Map<String, Object> item = new HashMap<String, Object>();
            item.put("ingredientName", ing.getIngredientName());
            item.put("amount", ing.getAmount());
            item.put("unit", ing.getUnit());

            Food matched = findBestFoodMatch(ing.getIngredientName(), allFoods);
            if (matched != null) {
                double ratio = 1.0;
                if (ing.getAmount() != null && ing.getUnit() != null && "g".equals(ing.getUnit())) {
                    ratio = ing.getAmount().doubleValue() / 100.0;
                }
                item.put("calories", matched.getCalorie() != null ? matched.getCalorie().doubleValue() * ratio : 0);
                item.put("protein", matched.getProtein() != null ? matched.getProtein().doubleValue() * ratio : 0);
                item.put("fat", matched.getFat() != null ? matched.getFat().doubleValue() * ratio : 0);
                item.put("carbs", matched.getCarb() != null ? matched.getCarb().doubleValue() * ratio : 0);
                item.put("foodCategory", matched.getFoodCategory());

                boolean showGi = matched.getShowGi() != null && matched.getShowGi() == 1;
                boolean showFolicAcid = matched.getShowFolicAcid() != null && matched.getShowFolicAcid() == 1;
                boolean showDha = matched.getShowDha() != null && matched.getShowDha() == 1;

                if (showGi && matched.getGiValue() != null && totalWeight > 0) {
                    double weightRatio = (ing.getAmount() != null && ing.getUnit() != null && "g".equals(ing.getUnit()))
                            ? ing.getAmount().doubleValue() / totalWeight : 0;
                    item.put("giContribution", matched.getGiValue().doubleValue() * weightRatio);
                }
                if (showFolicAcid && matched.getFolicAcid() != null) {
                    item.put("folicAcid", matched.getFolicAcid().doubleValue() * ratio);
                }
                if (showDha && matched.getDha() != null) {
                    item.put("dha", matched.getDha().doubleValue() * ratio);
                }
            }
            result.add(item);
        }
        return result;
    }

    /**
     * 计算替换后营养变化（估算）
     */
    @SuppressWarnings("unchecked")
    private Map<String, Object> calculatePotentialNutritionChange(
            List<Map<String, Object>> substitutions,
            List<Map<String, Object>> foodDbSubstitutions,
            List<Map<String, Object>> ingredientNutrition) {
        
        double totalSavedCalories = 0;
        double totalSavedFat = 0;
        double totalSavedSugar = 0;
        double totalAddedProtein = 0;
        int replaceableCount = 0;
        
        // 基于foodDbSubstitutions估算
        for (Map<String, Object> sub : foodDbSubstitutions) {
            List<String> concerns = (List<String>) sub.get("concerns");
            List<Map<String, Object>> alternatives = (List<Map<String, Object>>) sub.get("alternatives");
            if (alternatives == null || alternatives.isEmpty()) continue;
            
            Map<String, Object> bestAlt = alternatives.get(0);
            replaceableCount++;
            
            for (String concern : concerns) {
                if (concern.startsWith("高脂")) {
                    Number altFat = (Number) bestAlt.get("fat");
                    if (altFat != null) {
                        // 假设替换可减少约30-50%该食材营养问题
                        totalSavedFat += 10;
                    }
                }
                if (concern.startsWith("高热量")) {
                    Number altCal = (Number) bestAlt.get("calories");
                    Number origCal = (Number) sub.get("calories");
                    if (altCal != null && origCal != null) {
                        totalSavedCalories += origCal.doubleValue() - altCal.doubleValue();
                    } else {
                        totalSavedCalories += 50;
                    }
                }
            }
        }
        
        Map<String, Object> change = new HashMap<String, Object>();
        change.put("calories", -Math.round(totalSavedCalories));
        change.put("fat", -Math.round(totalSavedFat));
        change.put("protein", Math.round(totalAddedProtein));
        change.put("replaceableCount", replaceableCount);
        change.put("hasChanges", replaceableCount > 0);
        return change;
    }

    /**
     * 在食物数据库中智能匹配食材名称（5级匹配）
     */
    Food findBestFoodMatch(String ingredientName, List<Food> allFoods) {
        if (allFoods == null || allFoods.isEmpty()) return null;
        
        // 0级：同义词映射匹配
        String standardName = FOOD_ALIASES.get(ingredientName);
        if (standardName != null) {
            for (Food f : allFoods) {
                if (f.getFoodName().equals(standardName)) return f;
            }
        }
        
        // 1级：精确匹配
        for (Food f : allFoods) {
            if (f.getFoodName().equals(ingredientName)) return f;
        }
        
        // 2级：食物名包含食材名（最常用，处理 "鸡胸肉" → "鸡胸肉"）
        for (Food f : allFoods) {
            if (f.getFoodName().contains(ingredientName)) return f;
        }
        
        // 3级：食材名包含食物名（处理 "姜片" → "生姜" 等常用映射已在第0级处理）
        for (Food f : allFoods) {
            if (ingredientName.contains(f.getFoodName())) return f;
        }
        
        // 4级：食材名包含食物核心名的主要字符（多字匹配，防误匹配）
        for (Food f : allFoods) {
            String coreName = f.getFoodName().replaceAll("\\(.*\\)", "").trim();
            if (ingredientName.contains(coreName)) return f;
        }
        
        return null;
    }

    /**
     * 增强版食材分析：使用规则引擎 + 过敏原映射
     * 参考 Demo substituteRules.ts 的 annotateIngredients 逻辑
     */
    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> analyzeIngredients(List<RecipeIngredient> ingredients, User user) {
        List<Map<String, Object>> substitutions = new ArrayList<Map<String, Object>>();
        
        Set<String> allergicFoods = new HashSet<String>();
        Set<String> restrictions = new HashSet<String>();
        String tastePreference = "清淡";
        
        if (user != null) {
            if (user.getAllergicFoods() != null) {
                for (String food : user.getAllergicFoods().split(",")) {
                    allergicFoods.add(food.trim());
                }
            }
            if (user.getDietaryRestrictions() != null) {
                for (String restriction : user.getDietaryRestrictions().split(",")) {
                    restrictions.add(restriction.trim());
                }
            }
            if (user.getTastePreference() != null) {
                tastePreference = user.getTastePreference();
            }
        }
        
        for (RecipeIngredient ingredient : ingredients) {
            String ingredientName = ingredient.getIngredientName();
            boolean alreadyNotSuitable = false;
            
            // ===== 1. 过敏原检测（使用 ALLERGEN_MATCH_TAGS） =====
            for (String allergy : allergicFoods) {
                List<String> matchTags = ALLERGEN_MATCH_TAGS.getOrDefault(allergy, Arrays.asList(allergy.toLowerCase()));
                boolean isMatch = false;
                for (String tag : matchTags) {
                    if (ingredientName.contains(tag) || tag.contains(ingredientName)) {
                        isMatch = true;
                        break;
                    }
                }
                if (isMatch) {
                    Map<String, Object> sub = new HashMap<String, Object>();
                    sub.put("ingredient", ingredient);
                    sub.put("isNotSuitable", true);
                    sub.put("substitutionType", "allergy");
                    sub.put("reason", "含过敏原：" + allergy);
                    
                    // 过敏替代推荐
                    List<Map<String, String>> altList = new ArrayList<Map<String, String>>();
                    Map<String, String> alt1 = new HashMap<String, String>();
                    alt1.put("name", "可省略此食材");
                    alt1.put("benefit", "建议直接省略");
                    altList.add(alt1);
                    Map<String, String> alt2 = new HashMap<String, String>();
                    alt2.put("name", "咨询营养师");
                    alt2.put("benefit", "获取个性化建议");
                    altList.add(alt2);
                    sub.put("alternatives", altList);
                    substitutions.add(sub);
                    alreadyNotSuitable = true;
                    break;
                }
            }
            if (alreadyNotSuitable) continue;
            
            // ===== 2. 规则引擎匹配（低脂/低盐/低糖/糖尿病/清淡） =====
            Set<String> activeRestrictions = new HashSet<String>(restrictions);
            if (!"清淡".equals(tastePreference)) {
                activeRestrictions.add(tastePreference);
            }
            // 清淡口味默认加无辣限制
            if ("清淡".equals(tastePreference)) {
                activeRestrictions.add("清淡");
            }
            
            for (Map<String, Object> rule : SUBSTITUTION_RULES) {
                String ruleRestriction = (String) rule.get("restriction");
                if (!activeRestrictions.contains(ruleRestriction)) continue;
                
                List<String> keywords = (List<String>) rule.get("keywords");
                boolean matched = false;
                for (String kw : keywords) {
                    if (ingredientName.contains(kw)) {
                        matched = true;
                        break;
                    }
                }
                
                if (matched) {
                    Map<String, Object> sub = new HashMap<String, Object>();
                    sub.put("ingredient", ingredient);
                    sub.put("isNotSuitable", true);
                    sub.put("substitutionType", ruleRestriction);
                    sub.put("reason", (String) rule.get("reason"));
                    sub.put("alternatives", rule.get("alternatives"));
                    substitutions.add(sub);
                    break;
                }
            }
        }
        
        return substitutions;
    }

    /**
     * 基于食物数据库的智能替换分析：
     * 检查每种食材的营养指标（高脂/高GI/高热量），从同类别中推荐更优替代
     */
    private List<Map<String, Object>> analyzeIngredientsWithFoodDB(List<RecipeIngredient> ingredients) {
        List<Map<String, Object>> result = new ArrayList<Map<String, Object>>();
        List<Food> allFoods = foodRepository.findAll();

        for (RecipeIngredient ingredient : ingredients) {
            String name = ingredient.getIngredientName();
            // 使用统一的 findBestFoodMatch 查找匹配食材
            Food food = findBestFoodMatch(name, allFoods);
            if (food == null) continue;

            List<String> concerns = new ArrayList<String>();
            List<Map<String, Object>> alternatives = new ArrayList<Map<String, Object>>();

            // 检查高脂
            if (food.getFat() != null && food.getFat().doubleValue() > HIGH_FAT_THRESHOLD) {
                concerns.add("高脂(" + food.getFat() + "g/100g)");
                for (Food alt : allFoods) {
                    if (alt.getFoodId().equals(food.getFoodId())) continue;
                    if (!alt.getFoodCategory().equals(food.getFoodCategory())) continue;
                    if (alt.getFat() != null && alt.getFat().doubleValue() <= food.getFat().doubleValue() * 0.7) {
                        Map<String, Object> altMap = new HashMap<String, Object>();
                        altMap.put("name", alt.getFoodName());
                        altMap.put("calories", alt.getCalorie());
                        altMap.put("fat", alt.getFat());
                        altMap.put("protein", alt.getProtein());
                        altMap.put("reason", "低脂替代(减少" + (int)((1 - alt.getFat().doubleValue()/food.getFat().doubleValue())*100) + "%脂肪)");
                        alternatives.add(altMap);
                    }
                }
            }

            // 检查高GI（仅当没有高脂问题时才报GI，或已有替代方案时才GI需额外补充）
            if (food.getGiValue() != null && food.getGiValue().doubleValue() > HIGH_GI_THRESHOLD) {
                concerns.add("高GI(" + food.getGiValue() + ")");
                if (alternatives.isEmpty()) {
                    for (Food alt : allFoods) {
                        if (alt.getFoodId().equals(food.getFoodId())) continue;
                        if (!alt.getFoodCategory().equals(food.getFoodCategory())) continue;
                        if (alt.getGiValue() != null && alt.getGiValue().doubleValue() <= food.getGiValue().doubleValue() * 0.8) {
                            Map<String, Object> altMap = new HashMap<String, Object>();
                            altMap.put("name", alt.getFoodName());
                            altMap.put("calories", alt.getCalorie());
                            altMap.put("fat", alt.getFat());
                            altMap.put("giValue", alt.getGiValue());
                            altMap.put("reason", "低GI替代(低" + (int)(food.getGiValue().doubleValue() - alt.getGiValue().doubleValue()) + ")");
                            alternatives.add(altMap);
                        }
                    }
                }
            }

            // 检查高热量（仅当无更高优先级问题时）
            if (food.getCalorie() != null && food.getCalorie().doubleValue() > HIGH_CALORIE_THRESHOLD && concerns.isEmpty()) {
                concerns.add("高热量(" + food.getCalorie() + "kcal/100g)");
                if (alternatives.isEmpty()) {
                    for (Food alt : allFoods) {
                        if (alt.getFoodId().equals(food.getFoodId())) continue;
                        if (!alt.getFoodCategory().equals(food.getFoodCategory())) continue;
                        if (alt.getCalorie() != null && alt.getCalorie().doubleValue() <= food.getCalorie().doubleValue() * 0.75) {
                            Map<String, Object> altMap = new HashMap<String, Object>();
                            altMap.put("name", alt.getFoodName());
                            altMap.put("calories", alt.getCalorie());
                            altMap.put("fat", alt.getFat());
                            altMap.put("protein", alt.getProtein());
                            altMap.put("reason", "低热量替代(减少" + (int)((1 - alt.getCalorie().doubleValue()/food.getCalorie().doubleValue())*100) + "%热量)");
                            alternatives.add(altMap);
                        }
                    }
                }
            }

            if (!concerns.isEmpty()) {
                Map<String, Object> sub = new HashMap<String, Object>();
                sub.put("ingredientName", name);
                sub.put("amount", ingredient.getAmount() + ingredient.getUnit());
                sub.put("concerns", concerns);
                sub.put("alternatives", alternatives.subList(0, Math.min(3, alternatives.size())));
                result.add(sub);
            }
        }
        return result;
    }

    /**
     * 从请求数据创建食谱（Map版本）
     */
    @Caching(evict = {
            @CacheEvict(cacheNames = "recipeSearch", allEntries = true),
            @CacheEvict(cacheNames = "recipeById", allEntries = true),
            @CacheEvict(cacheNames = "recipeByTag", allEntries = true),
            @CacheEvict(cacheNames = "recipeAll", allEntries = true)
    })
    @Transactional
    public Recipe saveRecipe(Integer userId, Map<String, Object> recipeData) {
        Recipe recipe = new Recipe();
        recipe.setRecipeName(String.valueOf(recipeData.getOrDefault("name", recipeData.getOrDefault("recipeName", ""))));
        recipe.setDescription(String.valueOf(recipeData.getOrDefault("description", "")));
        Object calObj = recipeData.get("calories");
        if (calObj != null) {
            recipe.setCalories(new BigDecimal(String.valueOf(calObj)));
        }
        Object proObj = recipeData.get("protein");
        if (proObj != null) {
            recipe.setProtein(new BigDecimal(String.valueOf(proObj)));
        }
        Object fatObj = recipeData.get("fat");
        if (fatObj != null) {
            recipe.setFat(new BigDecimal(String.valueOf(fatObj)));
        }
        Object carbObj = recipeData.get("carbs");
        if (carbObj != null) {
            recipe.setCarbs(new BigDecimal(String.valueOf(carbObj)));
        }
        Object fiberObj = recipeData.get("fiber");
        if (fiberObj != null) {
            recipe.setFiber(new BigDecimal(String.valueOf(fiberObj)));
        }
        recipe.setTags(String.valueOf(recipeData.getOrDefault("tags", "")));
        return recipeRepository.save(recipe);
    }

    /**
     * 更新食谱（Map版本，用于Admin）
     */
    @Caching(evict = {
            @CacheEvict(cacheNames = "recipeSearch", allEntries = true),
            @CacheEvict(cacheNames = "recipeById", allEntries = true),
            @CacheEvict(cacheNames = "recipeByTag", allEntries = true),
            @CacheEvict(cacheNames = "recipeAll", allEntries = true)
    })
    @Transactional
    public Recipe updateRecipe(Integer recipeId, Map<String, Object> recipeData) {
        Recipe existing = recipeRepository.findById(recipeId).orElse(null);
        if (existing == null) return null;

        if (recipeData.containsKey("recipeName") || recipeData.containsKey("name")) {
            existing.setRecipeName(String.valueOf(recipeData.getOrDefault("name", recipeData.get("recipeName"))));
        }
        if (recipeData.containsKey("description")) {
            existing.setDescription(String.valueOf(recipeData.get("description")));
        }
        if (recipeData.containsKey("calories")) {
            existing.setCalories(new BigDecimal(String.valueOf(recipeData.get("calories"))));
        }
        if (recipeData.containsKey("protein")) {
            existing.setProtein(new BigDecimal(String.valueOf(recipeData.get("protein"))));
        }
        if (recipeData.containsKey("fat")) {
            existing.setFat(new BigDecimal(String.valueOf(recipeData.get("fat"))));
        }
        if (recipeData.containsKey("carbs")) {
            existing.setCarbs(new BigDecimal(String.valueOf(recipeData.get("carbs"))));
        }
        if (recipeData.containsKey("fiber")) {
            existing.setFiber(new BigDecimal(String.valueOf(recipeData.get("fiber"))));
        }
        if (recipeData.containsKey("tags")) {
            existing.setTags(String.valueOf(recipeData.get("tags")));
        }

        return recipeRepository.save(existing);
    }

    @Cacheable(cacheNames = "recipeByTag", key = "#tag")
    public List<Recipe> getRecipesByTag(String tag) {
        return recipeRepository.findByTagsContaining(tag);
    }

    @Cacheable(cacheNames = "recipeAll")
    public List<Recipe> getAllRecipes() {
        return recipeRepository.findAll();
    }

    public List<SavedRecipe> getSavedRecipes(Integer userId) {
        return savedRecipeRepository.findByUserIdOrderByCreatedAtDesc(userId);
    }

    @Transactional
    public SavedRecipe saveUserRecipe(Integer userId, Map<String, Object> recipeData) {
        SavedRecipe savedRecipe = new SavedRecipe();
        savedRecipe.setUserId(userId);
        savedRecipe.setTitle(String.valueOf(recipeData.get("title")));
        savedRecipe.setIngredients(String.valueOf(recipeData.getOrDefault("ingredients", "")));
        savedRecipe.setSteps(String.valueOf(recipeData.getOrDefault("steps", "")));
        savedRecipe.setNutritionSummary(String.valueOf(recipeData.getOrDefault("nutritionSummary", "")));
        savedRecipe.setPersonaTag(String.valueOf(recipeData.getOrDefault("personaTag", "")));
        return savedRecipeRepository.save(savedRecipe);
    }

    public void deleteSavedRecipe(Integer userId, Integer savedId) {
        savedRecipeRepository.deleteByIdAndUserId(savedId, userId);
    }
}