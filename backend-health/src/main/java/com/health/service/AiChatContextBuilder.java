package com.health.service;

import com.health.entity.*;
import com.health.repository.*;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.*;

/**
 * AI 咨询上下文构建器：负责把用户历史数据组装成 AI 可用的健康快照与系统提示词。
 *
 * 从原 AiChatService 拆分出的「上下文组装域」：
 * - 健康数据快照（用户资料 / 今日身体指标 / 今日饮食 / 近7日运动 / 趋势 / 饮食参考）
 * - 后端预计算目标值（BMR / 活动系数 / 热量与营养素目标）
 * - 发给 AI 服务的分层系统提示词
 *
 * 职责单一：只做数据读取与组装，不发起任何 AI HTTP 调用。
 */
@Service
public class AiChatContextBuilder {

    private final BodyMetricsHistoryRepository historyRepository;
    private final DietMealRepository dietMealRepository;
    private final DietItemRepository dietItemRepository;
    private final FoodRepository foodRepository;
    private final ExerciseRecordRepository exerciseRecordRepository;

    public AiChatContextBuilder(BodyMetricsHistoryRepository historyRepository,
                                DietMealRepository dietMealRepository,
                                DietItemRepository dietItemRepository,
                                FoodRepository foodRepository,
                                ExerciseRecordRepository exerciseRecordRepository) {
        this.historyRepository = historyRepository;
        this.dietMealRepository = dietMealRepository;
        this.dietItemRepository = dietItemRepository;
        this.foodRepository = foodRepository;
        this.exerciseRecordRepository = exerciseRecordRepository;
    }

    /**
     * 构建用户健康数据快照：用户资料 + 今日身体指标 + 今日饮食记录
     */
    public Map<String, Object> buildHealthSnapshot(User user, String date) {
        Map<String, Object> snapshot = new LinkedHashMap<>();
        snapshot.put("date", date);

        // 用户资料
        Map<String, Object> profile = new LinkedHashMap<>();
        profile.put("username", user.getUsername());
        profile.put("gender", user.getGender());
        profile.put("age", user.getAge());
        profile.put("height_cm", user.getHeight());
        profile.put("weight_kg", user.getWeight());
        double bmi = 0;
        if (user.getHeight() != null && user.getWeight() != null && user.getHeight() > 0) {
            double h = user.getHeight() / 100.0;
            bmi = user.getWeight() / (h * h);
            bmi = Math.round(bmi * 10.0) / 10.0;
        }
        profile.put("bmi", bmi);
        profile.put("crowdType", user.getCrowdType());
        snapshot.put("profile", profile);

        // 今日身体指标
        Map<String, Object> todayMetrics = new LinkedHashMap<>();
        Optional<BodyMetricsHistory> history = historyRepository.findByUserIdAndRecordDate(user.getUserId(), date);
        if (history.isPresent()) {
            BodyMetricsHistory h = history.get();
            todayMetrics.put("date", h.getRecordDate());
            todayMetrics.put("height_cm", h.getHeight());
            todayMetrics.put("weight_kg", h.getWeight());
            todayMetrics.put("age", h.getAge());
            todayMetrics.put("bmr", h.getBmr());
            double todayBmi = 0;
            if (h.getHeight() != null && h.getWeight() != null && h.getHeight() > 0) {
                double hh = h.getHeight() / 100.0;
                todayBmi = h.getWeight() / (hh * hh);
                todayBmi = Math.round(todayBmi * 10.0) / 10.0;
            }
            todayMetrics.put("bmi", todayBmi);
        } else {
            todayMetrics.put("note", "今日暂无身体指标记录快照，使用用户资料中的数据");
            todayMetrics.put("height_cm", user.getHeight());
            todayMetrics.put("weight_kg", user.getWeight());
            todayMetrics.put("age", user.getAge());
            todayMetrics.put("bmi", bmi);
        }
        snapshot.put("today_body_metrics", todayMetrics);

        // 今日饮食记录（按 meal_type 合并同类餐次，避免 9 次添加显示为 9 餐）
        List<Map<String, Object>> dietList = new ArrayList<>();
        List<DietMeal> meals = dietMealRepository.findByUserIdAndEatDate(user.getUserId(), date);
        BigDecimal totalCalorie = BigDecimal.ZERO;
        BigDecimal totalProtein = BigDecimal.ZERO;
        BigDecimal totalFat = BigDecimal.ZERO;
        BigDecimal totalCarb = BigDecimal.ZERO;
        int totalFoodItems = 0;

        // 建立 mealId -> meal 映射
        Map<Integer, DietMeal> mealMap = new LinkedHashMap<>();
        for (DietMeal meal : meals) {
            mealMap.put(meal.getMealId(), meal);
        }

        // 批量加载所有餐次的饮食明细与食物（避免 N+1 查询）
        Map<Integer, List<DietItem>> itemsByMeal = new HashMap<>();
        Map<Integer, Food> foodMap = new HashMap<>();
        if (meals != null && !meals.isEmpty()) {
            List<Integer> mealIds = new ArrayList<>();
            for (DietMeal meal : meals) {
                mealIds.add(meal.getMealId());
            }
            List<DietItem> allItems = dietItemRepository.findByMealIdIn(mealIds);
            if (allItems != null) {
                for (DietItem item : allItems) {
                    itemsByMeal.computeIfAbsent(item.getMealId(), k -> new ArrayList<>()).add(item);
                }
            }
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
        }

        // 按 meal_type 分组：meal_type -> List<item data>
        Map<String, List<Map<String, Object>>> groupedFoods = new LinkedHashMap<>();
        Map<String, BigDecimal> mealTypeCalories = new LinkedHashMap<>();
        Map<String, List<String>> mealTypeRemarks = new LinkedHashMap<>();

        for (DietMeal meal : meals) {
            String mealType = meal.getMealType();
            // 收集该餐次的备注
            if (meal.getRemark() != null && !meal.getRemark().trim().isEmpty()) {
                mealTypeRemarks.computeIfAbsent(mealType, k -> new ArrayList<>()).add(meal.getRemark());
            }
            List<DietItem> dietItems = itemsByMeal.getOrDefault(meal.getMealId(), Collections.emptyList());

            for (DietItem item : dietItems) {
                Food food = foodMap.get(item.getFoodId());
                if (food != null) {
                    Map<String, Object> itemData = new LinkedHashMap<>();
                    itemData.put("food_name", food.getFoodName());
                    itemData.put("category", food.getFoodCategory());
                    itemData.put("eat_weight_g", item.getEatWeight());

                    BigDecimal factor = item.getEatWeight() != null
                            ? item.getEatWeight().divide(new BigDecimal("100"), 4, BigDecimal.ROUND_HALF_UP)
                            : BigDecimal.ZERO;
                    BigDecimal calorie = food.getCalorie() != null ? food.getCalorie().multiply(factor) : BigDecimal.ZERO;
                    BigDecimal protein = food.getProtein() != null ? food.getProtein().multiply(factor) : BigDecimal.ZERO;
                    BigDecimal fat = food.getFat() != null ? food.getFat().multiply(factor) : BigDecimal.ZERO;
                    BigDecimal carb = food.getCarb() != null ? food.getCarb().multiply(factor) : BigDecimal.ZERO;

                    itemData.put("calories_kcal", calorie.setScale(1, BigDecimal.ROUND_HALF_UP));
                    itemData.put("protein_g", protein.setScale(1, BigDecimal.ROUND_HALF_UP));
                    itemData.put("fat_g", fat.setScale(1, BigDecimal.ROUND_HALF_UP));
                    itemData.put("carb_g", carb.setScale(1, BigDecimal.ROUND_HALF_UP));
                    if (food.getGiValue() != null) {
                        itemData.put("gi_value", food.getGiValue());
                    }

                    groupedFoods.computeIfAbsent(mealType, k -> new ArrayList<>()).add(itemData);
                    mealTypeCalories.merge(mealType, calorie, BigDecimal::add);

                    totalCalorie = totalCalorie.add(calorie);
                    totalProtein = totalProtein.add(protein);
                    totalFat = totalFat.add(fat);
                    totalCarb = totalCarb.add(carb);
                    totalFoodItems++;
                }
            }
        }

        // 构建合并后的餐次列表
        for (Map.Entry<String, List<Map<String, Object>>> entry : groupedFoods.entrySet()) {
            Map<String, Object> mealData = new LinkedHashMap<>();
            mealData.put("meal_type", entry.getKey());
            mealData.put("foods", entry.getValue());
            mealData.put("food_items_count", entry.getValue().size());
            mealData.put("meal_calories_kcal", mealTypeCalories.get(entry.getKey()).setScale(1, BigDecimal.ROUND_HALF_UP));
            // 合并同类型餐次的备注
            List<String> remarks = mealTypeRemarks.get(entry.getKey());
            if (remarks != null && !remarks.isEmpty()) {
                mealData.put("remark", String.join("；", remarks));
            }
            dietList.add(mealData);
        }

        Map<String, Object> total = new LinkedHashMap<>();
        total.put("total_calories_kcal", totalCalorie.setScale(1, BigDecimal.ROUND_HALF_UP));
        total.put("total_protein_g", totalProtein.setScale(1, BigDecimal.ROUND_HALF_UP));
        total.put("total_fat_g", totalFat.setScale(1, BigDecimal.ROUND_HALF_UP));
        total.put("total_carb_g", totalCarb.setScale(1, BigDecimal.ROUND_HALF_UP));
        total.put("total_food_items", totalFoodItems);
        total.put("total_meals", dietList.size());
        snapshot.put("today_diet", dietList);
        snapshot.put("today_diet_total", total);

        // 近 7 日运动数据（与身体数据一起作为建议依据）
        snapshot.put("recent_exercise", buildExerciseSnapshot(user.getUserId()));

        // 近 7 日身体指标趋势（体重/BMI 变化轨迹）
        snapshot.put("body_metrics_trend", buildBodyMetricsTrend(user.getUserId()));

        // 系统健康饮食参考
        snapshot.put("diet_reference", buildDietReference(user.getCrowdType()));

        return snapshot;
    }

    /**
     * 构建近 7 日运动数据快照：训练频次、总时长、总消耗、按类型分布、每日明细。
     * 作为饮食建议与训练计划的双重数据源之一。
     */
    public Map<String, Object> buildExerciseSnapshot(Integer userId) {
        Map<String, Object> exerciseSnapshot = new LinkedHashMap<>();
        LocalDate end = LocalDate.now();
        LocalDate start = end.minusDays(6); // 含今日共 7 天
        List<ExerciseRecord> records = exerciseRecordRepository
                .findByUserIdAndRecordDateBetweenOrderByRecordDateDesc(userId, start, end);

        if (records == null || records.isEmpty()) {
            exerciseSnapshot.put("note", "近 7 日暂无运动记录");
            exerciseSnapshot.put("total_sessions", 0);
            exerciseSnapshot.put("total_duration_min", 0);
            exerciseSnapshot.put("total_calories_burned", 0);
            return exerciseSnapshot;
        }

        int totalDuration = 0;
        double totalCalories = 0;
        Map<String, int[]> typeStats = new LinkedHashMap<>(); // type -> [count, duration]
        Map<String, Double> typeCalories = new LinkedHashMap<>();
        Map<String, List<Map<String, Object>>> dailyDetail = new LinkedHashMap<>();

        for (ExerciseRecord r : records) {
            int dur = r.getDurationMin() != null ? r.getDurationMin() : 0;
            double cal = r.getCaloriesBurned() != null ? r.getCaloriesBurned() : 0;
            totalDuration += dur;
            totalCalories += cal;

            String type = r.getExerciseType() != null ? r.getExerciseType() : "其他";
            typeStats.computeIfAbsent(type, k -> new int[]{0, 0});
            typeStats.get(type)[0]++;
            typeStats.get(type)[1] += dur;
            typeCalories.merge(type, cal, Double::sum);

            String dateKey = r.getRecordDate() != null ? r.getRecordDate().toString() : "未知日期";
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("exercise_type", type);
            item.put("duration_min", dur);
            item.put("calories_burned", Math.round(cal * 10.0) / 10.0);
            item.put("note", r.getNote());
            dailyDetail.computeIfAbsent(dateKey, k -> new ArrayList<>()).add(item);
        }

        exerciseSnapshot.put("date_range", start.toString() + " ~ " + end.toString());
        exerciseSnapshot.put("total_sessions", records.size());
        exerciseSnapshot.put("total_duration_min", totalDuration);
        exerciseSnapshot.put("total_calories_burned", Math.round(totalCalories * 10.0) / 10.0);

        // 按类型汇总
        List<Map<String, Object>> typeBreakdown = new ArrayList<>();
        for (Map.Entry<String, int[]> entry : typeStats.entrySet()) {
            Map<String, Object> t = new LinkedHashMap<>();
            t.put("exercise_type", entry.getKey());
            t.put("sessions", entry.getValue()[0]);
            t.put("duration_min", entry.getValue()[1]);
            t.put("calories_burned", Math.round(typeCalories.get(entry.getKey()) * 10.0) / 10.0);
            typeBreakdown.add(t);
        }
        exerciseSnapshot.put("type_breakdown", typeBreakdown);

        // 每日明细
        List<Map<String, Object>> dailyList = new ArrayList<>();
        for (Map.Entry<String, List<Map<String, Object>>> entry : dailyDetail.entrySet()) {
            Map<String, Object> d = new LinkedHashMap<>();
            d.put("date", entry.getKey());
            d.put("records", entry.getValue());
            dailyList.add(d);
        }
        exerciseSnapshot.put("daily_detail", dailyList);

        return exerciseSnapshot;
    }

    /**
     * 构建近 7 日身体指标趋势：体重/BMI 变化轨迹，用于判断趋势方向。
     */
    public Map<String, Object> buildBodyMetricsTrend(Integer userId) {
        Map<String, Object> trend = new LinkedHashMap<>();
        LocalDate end = LocalDate.now();
        LocalDate start = end.minusDays(6);
        String startStr = start.format(DateTimeFormatter.ISO_LOCAL_DATE);
        String endStr = end.format(DateTimeFormatter.ISO_LOCAL_DATE);

        List<BodyMetricsHistory> histories = historyRepository
                .findByUserIdAndRecordDateBetweenOrderByRecordDateDesc(userId, startStr, endStr);

        if (histories == null || histories.isEmpty()) {
            trend.put("note", "近 7 日暂无身体指标记录");
            return trend;
        }

        trend.put("date_range", startStr + " ~ " + endStr);
        trend.put("record_count", histories.size());

        // 按日期升序排列用于趋势展示
        List<BodyMetricsHistory> ascending = new ArrayList<>(histories);
        ascending.sort((a, b) -> {
            String da = a.getRecordDate() != null ? a.getRecordDate() : "";
            String db = b.getRecordDate() != null ? b.getRecordDate() : "";
            return da.compareTo(db);
        });

        List<Map<String, Object>> trendPoints = new ArrayList<>();
        Double firstWeight = null;
        Double lastWeight = null;
        for (BodyMetricsHistory h : ascending) {
            Map<String, Object> point = new LinkedHashMap<>();
            point.put("date", h.getRecordDate());
            point.put("weight_kg", h.getWeight());
            if (h.getHeight() != null && h.getWeight() != null && h.getHeight() > 0) {
                double hh = h.getHeight() / 100.0;
                double bmi = h.getWeight() / (hh * hh);
                point.put("bmi", Math.round(bmi * 10.0) / 10.0);
            }
            if (h.getBmr() != null) point.put("bmr", h.getBmr());
            trendPoints.add(point);

            if (firstWeight == null && h.getWeight() != null) firstWeight = h.getWeight().doubleValue();
            if (h.getWeight() != null) lastWeight = h.getWeight().doubleValue();
        }
        trend.put("trend_points", trendPoints);

        // 体重变化方向
        if (firstWeight != null && lastWeight != null) {
            double diff = Math.round((lastWeight - firstWeight) * 10.0) / 10.0;
            trend.put("weight_change_kg", diff);
            if (diff > 0.2) trend.put("weight_trend", "上升");
            else if (diff < -0.2) trend.put("weight_trend", "下降");
            else trend.put("weight_trend", "平稳");
        }

        return trend;
    }

    /**
     * 系统健康饮食参考知识（按人群类型给出参考标准）
     */
    public Map<String, Object> buildDietReference(String crowdType) {
        Map<String, Object> ref = new LinkedHashMap<>();

        // 通用饮食建议
        Map<String, String> general = new LinkedHashMap<>();
        general.put("bmi_normal_range", "18.5 - 23.9 (中国标准)");
        general.put("bmi_underweight", "< 18.5 偏瘦");
        general.put("bmi_overweight", ">= 24 超重");
        general.put("bmi_obese", ">= 28 肥胖");
        general.put("water_intake", "每日饮水 1500 - 2000 ml");
        general.put("meal_ratio", "早:午:晚 = 3:4:3");
        general.put("eat_speed", "细嚼慢咽，每餐 20-30 分钟");
        ref.put("general", general);

        // 人群特定建议
        Map<String, String> crowdSpecific = new LinkedHashMap<>();
        if ("健身".equals(crowdType)) {
            crowdSpecific.put("protein_target", "1.6 - 2.2 g/kg 体重/天");
            crowdSpecific.put("advice", "高蛋白、适量碳水、健康脂肪。训练后30分钟内补充蛋白质20-30g。");
        } else if ("青少年".equals(crowdType)) {
            crowdSpecific.put("protein_target", "1.2 - 1.5 g/kg 体重/天");
            crowdSpecific.put("advice", "足够热量和蛋白质，足量钙和维生素D，规律三餐。");
        } else if ("老年".equals(crowdType)) {
            crowdSpecific.put("protein_target", "1.2 - 1.4 g/kg 体重/天");
            crowdSpecific.put("advice", "高蛋白、充足钙与维生素D，少食多餐，低盐低油。");
        } else if ("孕妇".equals(crowdType)) {
            crowdSpecific.put("protein_target", "1.3 - 1.6 g/kg 体重/天");
            crowdSpecific.put("advice", "足量叶酸、钙、铁、DHA；避免生冷、生的肉蛋类；禁酒。");
        } else if ("糖尿病".equals(crowdType)) {
            crowdSpecific.put("protein_target", "1.1 - 1.3 g/kg 体重/天");
            crowdSpecific.put("advice", "低GI饮食、少食多餐、控制碳水总量、限制精制糖；餐后适度运动。");
        } else {
            crowdSpecific.put("protein_target", "1.0 - 1.2 g/kg 体重/天");
            crowdSpecific.put("advice", "均衡饮食，每日蔬果谷蛋奶肉齐全，规律运动，充足睡眠。");
        }
        ref.put("crowd_specific", crowdSpecific);

        // 食物GI值参考
        Map<String, String> giRef = new LinkedHashMap<>();
        giRef.put("low_gi", "GI < 55：糙米、燕麦、荞麦、红薯、苹果、梨、酸奶、大多数蔬菜");
        giRef.put("medium_gi", "GI 55-70：全麦面包、糙米、香蕉、玉米、葡萄");
        giRef.put("high_gi", "GI > 70：白米饭、白面包、糯米、含糖饮料、西瓜、麦芽糖");
        ref.put("gi_reference", giRef);

        return ref;
    }

}
