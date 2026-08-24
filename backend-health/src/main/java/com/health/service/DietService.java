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
import com.health.util.NutritionCalculator;
import com.health.vo.DietItemVO;
import com.health.vo.DietMealVO;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import lombok.extern.slf4j.Slf4j;

import java.math.BigDecimal;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
public class DietService {

    private final DietMealRepository dietMealRepository;
    private final DietItemRepository dietItemRepository;
    private final FoodRepository foodRepository;
    private final UserRepository userRepository;

    public DietService(DietMealRepository dietMealRepository, DietItemRepository dietItemRepository,
                       FoodRepository foodRepository, UserRepository userRepository) {
        this.dietMealRepository = dietMealRepository;
        this.dietItemRepository = dietItemRepository;
        this.foodRepository = foodRepository;
        this.userRepository = userRepository;
    }

    @Transactional
    public DietMeal addMeal(Integer userId, AddMealRequest request) {
        DietMeal meal = new DietMeal();
        meal.setUserId(userId);
        meal.setEatDate(request.getEatDate());
        meal.setMealType(request.getMealType());
        meal.setRemark(request.getRemark());
        meal = dietMealRepository.save(meal);

        for (AddMealRequest.MealItem item : request.getItems()) {
            DietItem dietItem = new DietItem();
            dietItem.setMealId(meal.getMealId());
            dietItem.setFoodId(item.getFoodId());
            dietItem.setEatWeight(item.getEatWeight());
            dietItemRepository.save(dietItem);
        }

        return meal;
    }

    /**
     * 删除一餐（级联删除其下所有 diet_item）。只有归属用户本人或其监护人可以删除。
     */
    @Transactional
    public boolean deleteMeal(Integer operateAs, Integer mealId) {
        return dietMealRepository.findById(mealId).map(meal -> {
            if (meal.getUserId() == null || !meal.getUserId().equals(operateAs)) return false;
            List<DietItem> items = dietItemRepository.findByMealId(mealId);
            if (items != null && !items.isEmpty()) dietItemRepository.deleteAll(items);
            dietMealRepository.delete(meal);
            return true;
        }).orElse(false);
    }

    public List<Map<String, Object>> getMealsByDate(Integer userId, String date) {
        List<DietMeal> meals = dietMealRepository.findByUserIdAndEatDate(userId, date);
        List<Map<String, Object>> result = new ArrayList<>();
        if (meals == null || meals.isEmpty()) {
            return result;
        }

        // 批量加载所有餐次的明细与食物（避免 N+1 查询）
        List<Integer> mealIds = new ArrayList<>();
        for (DietMeal meal : meals) {
            mealIds.add(meal.getMealId());
        }
        Map<Integer, List<DietItem>> itemsByMeal = new HashMap<>();
        List<DietItem> allItems = dietItemRepository.findByMealIdIn(mealIds);
        if (allItems != null) {
            for (DietItem item : allItems) {
                itemsByMeal.computeIfAbsent(item.getMealId(), k -> new ArrayList<>()).add(item);
            }
        }
        Map<Integer, Food> foodMap = new HashMap<>();
        Set<Integer> foodIds = new HashSet<>();
        for (List<DietItem> list : itemsByMeal.values()) {
            for (DietItem item : list) {
                foodIds.add(item.getFoodId());
            }
        }
        if (!foodIds.isEmpty()) {
            for (Food food : foodRepository.findAllById(foodIds)) {
                foodMap.put(food.getFoodId(), food);
            }
        }

        for (DietMeal meal : meals) {
            Map<String, Object> mealData = new HashMap<>();
            mealData.put("mealId", meal.getMealId());
            mealData.put("eatDate", meal.getEatDate());
            mealData.put("mealType", meal.getMealType());
            mealData.put("remark", meal.getRemark());

            List<DietItem> items = itemsByMeal.getOrDefault(meal.getMealId(), Collections.emptyList());
            List<Map<String, Object>> itemList = new ArrayList<>();

            for (DietItem item : items) {
                Food food = foodMap.get(item.getFoodId());
                if (food != null) {
                    Map<String, Object> itemData = new HashMap<>();
                    itemData.put("itemId", item.getItemId());
                    itemData.put("foodId", food.getFoodId());
                    itemData.put("foodName", food.getFoodName());
                    itemData.put("foodCategory", food.getFoodCategory());
                    itemData.put("eatWeight", item.getEatWeight());
                    itemData.put("calorie", food.getCalorie());
                    itemData.put("protein", food.getProtein());
                    itemData.put("fat", food.getFat());
                    itemData.put("carb", food.getCarb());
                    itemData.put("dietFiber", food.getDietFiber());
                    itemData.put("giValue", food.getGiValue());
                    itemData.put("calcium", food.getCalcium());
                    itemData.put("dha", food.getDha());
                    itemData.put("folicAcid", food.getFolicAcid());
                    itemList.add(itemData);
                }
            }
            mealData.put("items", itemList);
            result.add(mealData);
        }

        return result;
    }

    /**
     * 按日期查询餐次，返回 VO 列表（供前端直接使用）。
     */
    public List<DietMealVO> getMealsVO(Integer userId, String date) {
        List<DietMeal> meals = dietMealRepository.findByUserIdAndEatDate(userId, date);
        List<Food> allFoods = foodRepository.findAll();
        List<DietMealVO> result = new ArrayList<>();

        for (DietMeal meal : meals) {
            List<DietItem> items = dietItemRepository.findByMealId(meal.getMealId());
            List<Food> matchedFoods = new ArrayList<>();
            if (items != null) {
                for (DietItem item : items) {
                    Food food = allFoods.stream()
                            .filter(f -> f.getFoodId().equals(item.getFoodId()))
                            .findFirst().orElse(null);
                    matchedFoods.add(food);
                }
            }
            result.add(DietMealVO.fromEntity(meal, items, matchedFoods));
        }

        return result;
    }

    public Map<String, Object> analyzeDiet(Integer userId, String date) {
        User user = userRepository.findById(userId).orElseThrow(() -> new RuntimeException("用户不存在"));
        List<Map<String, Object>> meals = getMealsByDate(userId, date);

        BigDecimal totalCalorie = BigDecimal.ZERO;
        BigDecimal totalProtein = BigDecimal.ZERO;
        BigDecimal totalFat = BigDecimal.ZERO;
        BigDecimal totalCarb = BigDecimal.ZERO;
        BigDecimal totalDietFiber = BigDecimal.ZERO;
        BigDecimal totalCalcium = BigDecimal.ZERO;
        BigDecimal totalDha = BigDecimal.ZERO;
        BigDecimal totalFolicAcid = BigDecimal.ZERO;

        for (Map<String, Object> meal : meals) {
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> items = (List<Map<String, Object>>) meal.get("items");
            if (items != null) {
                for (Map<String, Object> item : items) {
                    BigDecimal weight = asBigDecimal(item.get("eatWeight"));
                    BigDecimal factor = weight.compareTo(BigDecimal.ZERO) == 0 ? BigDecimal.ZERO : weight.divide(new BigDecimal("100"), 4, BigDecimal.ROUND_HALF_UP);

                    totalCalorie = totalCalorie.add(mulOrZero(item.get("calorie"), factor));
                    totalProtein = totalProtein.add(mulOrZero(item.get("protein"), factor));
                    totalFat = totalFat.add(mulOrZero(item.get("fat"), factor));
                    totalCarb = totalCarb.add(mulOrZero(item.get("carb"), factor));
                    totalDietFiber = totalDietFiber.add(mulOrZero(item.get("dietFiber"), factor));
                    totalCalcium = totalCalcium.add(mulOrZero(item.get("calcium"), factor));
                    totalDha = totalDha.add(mulOrZero(item.get("dha"), factor));
                    totalFolicAcid = totalFolicAcid.add(mulOrZero(item.get("folicAcid"), factor));
                }
            }
        }

        double bmr = NutritionCalculator.calculateBMR(user.getWeight(), user.getHeight(), user.getAge(), user.getGender());
        double intakeBmrRatio = totalCalorie.doubleValue() / bmr;

        Map<String, double[]> nutrientRecs = getNutrientRecommendations(user.getCrowdType());
        Map<String, Object> result = new HashMap<>();

        Map<String, Object> userMap = new HashMap<>();
        userMap.put("weight", user.getWeight());
        userMap.put("height", user.getHeight());
        userMap.put("age", user.getAge());
        userMap.put("gender", user.getGender());
        userMap.put("crowdType", user.getCrowdType());
        userMap.put("bmr", bmr);
        userMap.put("intakeBmrRatio", intakeBmrRatio);
        userMap.put("recommendCalorieMin", bmr * getActivityMultiplier(user.getCrowdType())[0]);
        userMap.put("recommendCalorieMax", bmr * getActivityMultiplier(user.getCrowdType())[1]);
        result.put("user", userMap);

        Map<String, Object> totalMap = new HashMap<>();
        totalMap.put("calorie", totalCalorie.setScale(1, BigDecimal.ROUND_HALF_UP));
        totalMap.put("protein", totalProtein.setScale(1, BigDecimal.ROUND_HALF_UP));
        totalMap.put("fat", totalFat.setScale(1, BigDecimal.ROUND_HALF_UP));
        totalMap.put("carb", totalCarb.setScale(1, BigDecimal.ROUND_HALF_UP));
        totalMap.put("dietFiber", totalDietFiber.setScale(1, BigDecimal.ROUND_HALF_UP));
        totalMap.put("calcium", totalCalcium.setScale(1, BigDecimal.ROUND_HALF_UP));
        totalMap.put("dha", totalDha.setScale(1, BigDecimal.ROUND_HALF_UP));
        totalMap.put("folicAcid", totalFolicAcid.setScale(1, BigDecimal.ROUND_HALF_UP));
        result.put("total", totalMap);

        double weight = user.getWeight() != null ? user.getWeight() : 65;
        Map<String, Object> recMap = new HashMap<>();
        recMap.put("proteinMin", (nutrientRecs.get("protein")[0] * weight));
        recMap.put("proteinMax", (nutrientRecs.get("protein")[1] * weight));
        recMap.put("proteinPerKg", nutrientRecs.get("protein"));
        recMap.put("fatMin", (nutrientRecs.get("fat")[0] * weight));
        recMap.put("fatMax", (nutrientRecs.get("fat")[1] * weight));
        recMap.put("fatPerKg", nutrientRecs.get("fat"));
        recMap.put("carbMin", (nutrientRecs.get("carb")[0] * weight));
        recMap.put("carbMax", (nutrientRecs.get("carb")[1] * weight));
        recMap.put("carbPerKg", nutrientRecs.get("carb"));

        Map<String, Object> microRecs = getMicroNutrientRecommendations(user.getCrowdType());
        recMap.putAll(microRecs);
        result.put("recommendations", recMap);

        Map<String, Object> statusMap = new HashMap<>();
        statusMap.put("protein", checkStatus(totalProtein.doubleValue(), nutrientRecs.get("protein")[0] * weight, nutrientRecs.get("protein")[1] * weight));
        statusMap.put("fat", checkStatus(totalFat.doubleValue(), nutrientRecs.get("fat")[0] * weight, nutrientRecs.get("fat")[1] * weight));
        statusMap.put("carb", checkStatus(totalCarb.doubleValue(), nutrientRecs.get("carb")[0] * weight, nutrientRecs.get("carb")[1] * weight));
        statusMap.put("calcium", checkStatus(totalCalcium.doubleValue(), ((Number) microRecs.get("calciumMin")).doubleValue(), ((Number) microRecs.get("calciumMax")).doubleValue()));
        statusMap.put("folicAcid", checkStatus(totalFolicAcid.doubleValue(), ((Number) microRecs.get("folicAcidMin")).doubleValue(), ((Number) microRecs.get("folicAcidMax")).doubleValue()));
        statusMap.put("dietFiber", checkStatus(totalDietFiber.doubleValue(), ((Number) microRecs.get("dietFiberMin")).doubleValue(), ((Number) microRecs.get("dietFiberMax")).doubleValue()));
        statusMap.put("dha", checkStatus(totalDha.doubleValue(), ((Number) microRecs.get("dhaMin")).doubleValue(), ((Number) microRecs.get("dhaMax")).doubleValue()));
        result.put("status", statusMap);

        Map<String, String> warningsMap = new HashMap<>();
        addWarnings(warningsMap, "protein", statusMap.get("protein").toString(), totalProtein.doubleValue());
        addWarnings(warningsMap, "fat", statusMap.get("fat").toString(), totalFat.doubleValue());
        addWarnings(warningsMap, "carb", statusMap.get("carb").toString(), totalCarb.doubleValue());
        addWarnings(warningsMap, "calcium", statusMap.get("calcium").toString(), totalCalcium.doubleValue());
        addWarnings(warningsMap, "folicAcid", statusMap.get("folicAcid").toString(), totalFolicAcid.doubleValue());
        addWarnings(warningsMap, "dietFiber", statusMap.get("dietFiber").toString(), totalDietFiber.doubleValue());
        addWarnings(warningsMap, "dha", statusMap.get("dha").toString(), totalDha.doubleValue());
        result.put("warnings", warningsMap);

        result.put("meals", meals);

        log.info("饮食分析完成, userId={}, totalCalorie={}", userId, totalCalorie);
        return result;
    }

    private BigDecimal mulOrZero(Object value, BigDecimal factor) {
        if (value == null) return BigDecimal.ZERO;
        if (value instanceof BigDecimal) {
            return ((BigDecimal) value).multiply(factor);
        }
        if (value instanceof Number) {
            return BigDecimal.valueOf(((Number) value).doubleValue()).multiply(factor);
        }
        return BigDecimal.ZERO;
    }

    private BigDecimal asBigDecimal(Object value) {
        if (value == null) return BigDecimal.ZERO;
        if (value instanceof BigDecimal) return (BigDecimal) value;
        if (value instanceof Number) return BigDecimal.valueOf(((Number) value).doubleValue());
        try {
            return new BigDecimal(value.toString());
        } catch (Exception ignored) {
            return BigDecimal.ZERO;
        }
    }

    private double[] getActivityMultiplier(String crowdType) {
        switch (crowdType) {
            case "健身": return new double[]{1.6, 1.8};
            case "青少年": return new double[]{1.5, 1.7};
            case "孕妇": return new double[]{1.3, 1.5};
            case "老年": return new double[]{1.2, 1.4};
            case "糖尿病": return new double[]{1.2, 1.4};
            default: return new double[]{1.2, 1.5};
        }
    }

    private Map<String, double[]> getNutrientRecommendations(String crowdType) {
        Map<String, double[]> recs = new HashMap<>();
        switch (crowdType) {
            case "健身":
                recs.put("protein", new double[]{1.6, 2.2});
                recs.put("fat", new double[]{0.8, 1.0});
                recs.put("carb", new double[]{3.5, 5.0});
                break;
            case "青少年":
                recs.put("protein", new double[]{1.2, 1.5});
                recs.put("fat", new double[]{0.9, 1.1});
                recs.put("carb", new double[]{4.0, 5.0});
                break;
            case "老年":
                recs.put("protein", new double[]{1.2, 1.4});
                recs.put("fat", new double[]{0.7, 0.9});
                recs.put("carb", new double[]{2.0, 3.0});
                break;
            case "孕妇":
                recs.put("protein", new double[]{1.3, 1.6});
                recs.put("fat", new double[]{0.9, 1.1});
                recs.put("carb", new double[]{3.0, 4.0});
                break;
            case "糖尿病":
                recs.put("protein", new double[]{1.1, 1.3});
                recs.put("fat", new double[]{0.7, 0.9});
                recs.put("carb", new double[]{1.5, 2.5});
                break;
            default:
                recs.put("protein", new double[]{1.0, 1.2});
                recs.put("fat", new double[]{0.8, 1.0});
                recs.put("carb", new double[]{3.0, 4.0});
        }
        return recs;
    }

    private Map<String, Object> getMicroNutrientRecommendations(String crowdType) {
        Map<String, Object> recs = new HashMap<>();
        switch (crowdType) {
            case "孕妇":
                recs.put("calciumMin", 1000); recs.put("calciumMax", 1500);
                recs.put("folicAcidMin", 400); recs.put("folicAcidMax", 800);
                recs.put("dietFiberMin", 25); recs.put("dietFiberMax", 35);
                recs.put("dhaMin", 200); recs.put("dhaMax", 600);
                break;
            case "青少年":
                recs.put("calciumMin", 1000); recs.put("calciumMax", 1500);
                recs.put("folicAcidMin", 200); recs.put("folicAcidMax", 400);
                recs.put("dietFiberMin", 20); recs.put("dietFiberMax", 30);
                recs.put("dhaMin", 200); recs.put("dhaMax", 400);
                break;
            case "老年":
                recs.put("calciumMin", 1000); recs.put("calciumMax", 1500);
                recs.put("folicAcidMin", 200); recs.put("folicAcidMax", 400);
                recs.put("dietFiberMin", 25); recs.put("dietFiberMax", 35);
                recs.put("dhaMin", 200); recs.put("dhaMax", 400);
                break;
            case "糖尿病":
                recs.put("calciumMin", 800); recs.put("calciumMax", 1200);
                recs.put("folicAcidMin", 200); recs.put("folicAcidMax", 400);
                recs.put("dietFiberMin", 25); recs.put("dietFiberMax", 40);
                recs.put("dhaMin", 200); recs.put("dhaMax", 400);
                break;
            case "健身":
                recs.put("calciumMin", 800); recs.put("calciumMax", 1200);
                recs.put("folicAcidMin", 200); recs.put("folicAcidMax", 400);
                recs.put("dietFiberMin", 25); recs.put("dietFiberMax", 35);
                recs.put("dhaMin", 200); recs.put("dhaMax", 500);
                break;
            default:
                recs.put("calciumMin", 800); recs.put("calciumMax", 1200);
                recs.put("folicAcidMin", 200); recs.put("folicAcidMax", 400);
                recs.put("dietFiberMin", 20); recs.put("dietFiberMax", 35);
                recs.put("dhaMin", 100); recs.put("dhaMax", 300);
        }
        return recs;
    }

    private String checkStatus(double intake, double min, double max) {
        if (intake < min * 0.8) return "low";
        if (intake > max * 1.2) return "high";
        return "normal";
    }

    private void addWarnings(Map<String, String> warnings, String nutrient, String status, double intake) {
        String warning = "";
        switch (nutrient) {
            case "protein":
                if ("low".equals(status)) warning = "蛋白质摄入不足：肌肉流失、免疫力下降、运动恢复差";
                else if ("high".equals(status)) warning = "蛋白质摄入超标：加重肾脏负担、诱发痛风、热量过剩";
                break;
            case "fat":
                if ("low".equals(status)) warning = "脂肪摄入不足：脂溶性维生素吸收受阻、激素合成原料缺失";
                else if ("high".equals(status)) warning = "脂肪摄入超标：热量爆炸、高血脂、心血管负担增加";
                break;
            case "carb":
                if ("low".equals(status)) warning = "碳水摄入不足：大脑供能不足、头晕、运动无力、肌肉分解";
                else if ("high".equals(status)) warning = "碳水摄入超标：血糖波动、胰岛素抵抗、内脏脂肪堆积";
                break;
            case "calcium":
                if ("low".equals(status)) warning = "钙摄入不足：骨骼发育差、骨质疏松、腰酸背痛、抽筋";
                else if ("high".equals(status)) warning = "钙摄入超标：肾结石、血管钙化、影响铁锌吸收";
                break;
            case "folicAcid":
                if ("low".equals(status)) warning = "叶酸摄入不足：巨幼细胞贫血、口腔溃疡频发、脱发";
                else if ("high".equals(status)) warning = "叶酸摄入超标：掩盖B12缺乏、恶心腹胀、影响锌吸收";
                break;
            case "dietFiber":
                if ("low".equals(status)) warning = "膳食纤维不足：便秘、餐后血糖飙升、饱腹感弱";
                else if ("high".equals(status)) warning = "膳食纤维超标：腹胀排气多、矿物质吸收受阻";
                break;
            case "dha":
                if ("low".equals(status)) warning = "DHA摄入不足：记忆力下降、视力模糊、情绪调节变差";
                else if ("high".equals(status)) warning = "DHA摄入超标：出血风险上升、肠胃不适、恶心";
                break;
        }
        warnings.put(nutrient, warning);
    }
}