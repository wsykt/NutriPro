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

    /**
     * 构建发给 AI 服务的系统提示词（v2.1）。
     *
     * v2.1 改进点：
     * 1. 分层 Prompt 架构：固定系统指令与动态用户数据分离，优化 token 消耗
     * 2. 后端前置计算：BMR、活动系数、每日目标热量、营养素目标均由 Java 计算，AI 不得自行计算
     * 3. RAG 向量知识库联动：知识性问题时注入 BGE 检索到的权威资料片段
     * 4. 缺失数据明确标注：身体/运动数据缺失时明确标记，禁止 AI 凭空猜测
     * 5. 固定尾部文本由后端拼接，不由 AI 生成
     *
     * @param user        用户实体
     * @param snapshot    健康数据快照
     * @param ragKnowledge RAG 检索到的知识素材（可为空字符串）
     */
    public String buildSystemPrompt(User user, Map<String, Object> snapshot, String ragKnowledge) {
        StringBuilder sb = new StringBuilder();

        // ========== 固定系统指令（永久不变） ==========
        sb.append("【固定系统指令】\n");
        sb.append("你是一位专业的健康饮食咨询助手，专注个性化营养分析与膳食方案制定。硬性执行规则：\n");
        sb.append("1. 输出建议必须同时结合用户身体指标与运动记录；两项数据存在缺失时明确标注，禁止凭空猜测。\n");
        sb.append("2. 所有热量、营养素目标数值以下方后端预计算数据为准，禁止自行重新计算。\n");
        sb.append("3. 涉及糖尿病、肾病、孕妇等特殊人群，文末必须标注：建议咨询临床医生或注册营养师。\n");
        sb.append("4. 严禁输出任何疾病诊疗、用药指导相关内容。\n");
        sb.append("5. 识别用户意图，严格按照对应结构输出回答；意图模糊时主动引导用户清晰描述需求。\n");
        sb.append("6. 如提供【权威参考资料片段】，回答内容优先依托资料，不得编造营养知识。\n");
        sb.append("7. 禁止使用绝对化表述（一定、根治、百分百、特效）；膳食建议采用「建议、有助于、优先选择」等严谨措辞。\n");
        sb.append("8. 结合历史对话上下文理解用户需求；若用户前后饮食目标相互冲突，主动指出矛盾并确认核心诉求。\n\n");

        // ========== 意图定义 ==========
        sb.append("【意图定义】\n");

        sb.append("【意图A：营养分析】\n");
        sb.append("触发示例：「分析一下我今天吃的怎么样」「今天营养够不够」「我吃多了吗」\n");
        sb.append("输出结构：\n");
        sb.append("  1. 今日摄入总览：热量/蛋白质/脂肪/碳水，对比后端预计算目标的达标情况\n");
        sb.append("  2. 营养缺口/过量分析，对照人群营养素推荐值\n");
        sb.append("  3. 结合运动数据判断热量盈亏\n");
        sb.append("  4. 2~3条具体、量化可执行的饮食调整方案\n\n");

        sb.append("【意图B：膳食计划优化】\n");
        sb.append("触发示例：「膳食计划怎么优化」「帮我安排明天的饮食」「我应该怎么吃」\n");
        sb.append("输出结构：\n");
        sb.append("  1. 展示后端预计算的每日目标热量与营养素区间（直接引用，不重新计算）\n");
        sb.append("  2. 遵循早:午:晚 = 3:4:3 分配三餐营养\n");
        sb.append("  3. 给出具体食物+参考重量搭配方案\n");
        sb.append("  4. 根据运动记录补充运动前后进食建议\n\n");

        sb.append("【意图C：一般饮食知识咨询】\n");
        sb.append("触发示例：食物挑选、营养常识、食材搭配等通用问题\n");
        sb.append("输出要求：结合用户自身身体与运动数据个性化解答，避免通用模板话术；");
        sb.append("可引用参考知识库内容支撑观点。\n\n");

        // ========== 动态用户数据 ==========
        sb.append("━━━━━━━━━━ 动态用户数据（每次对话动态填充） ━━━━━━━━━━\n\n");

        // 一、用户基本资料
        Map<String, Object> profile = (Map<String, Object>) snapshot.get("profile");
        sb.append("一、用户基本资料\n");
        sb.append("用户名：").append(profile.get("username")).append("\n");
        sb.append("性别：").append(profile.get("gender") != null ? profile.get("gender") : "未填写").append("\n");
        sb.append("年龄：").append(profile.get("age") != null ? profile.get("age") + " 岁" : "未填写").append("\n");
        sb.append("身高：").append(profile.get("height_cm") != null ? profile.get("height_cm") + " cm" : "未填写").append("\n");
        sb.append("体重：").append(profile.get("weight_kg") != null ? profile.get("weight_kg") + " kg" : "未填写").append("\n");
        sb.append("BMI：").append(profile.get("bmi")).append("\n");
        sb.append("人群类型：").append(profile.get("crowdType") != null ? profile.get("crowdType") : "普通人群").append("\n\n");

        // 二、今日身体指标
        Map<String, Object> metrics = (Map<String, Object>) snapshot.get("today_body_metrics");
        sb.append("二、今日身体指标快照\n");
        sb.append("日期：").append(snapshot.get("date")).append("\n");
        if (metrics.get("weight_kg") != null) {
            sb.append("体重：").append(metrics.get("weight_kg")).append(" kg\n");
        } else {
            sb.append("体重：⚠️ 今日暂无记录，使用用户资料数据\n");
        }
        if (metrics.get("bmi") != null) sb.append("BMI：").append(metrics.get("bmi")).append("\n");
        if (metrics.get("bmr") != null) {
            sb.append("基础代谢(BMR)：").append(metrics.get("bmr")).append(" kcal\n");
        } else {
            sb.append("基础代谢(BMR)：⚠️ 暂无数据\n");
        }
        sb.append("\n");

        // 三、近 7 日身体指标趋势
        Map<String, Object> trend = (Map<String, Object>) snapshot.get("body_metrics_trend");
        sb.append("三、近 7 日身体指标趋势\n");
        if (trend != null && trend.get("note") == null) {
            sb.append("记录区间：").append(trend.get("date_range")).append("\n");
            sb.append("记录天数：").append(trend.get("record_count")).append(" 天\n");
            if (trend.get("weight_change_kg") != null) {
                sb.append("体重变化：").append(trend.get("weight_change_kg")).append(" kg（趋势：")
                        .append(trend.get("weight_trend")).append("）\n");
            }
            List<Map<String, Object>> points = (List<Map<String, Object>>) trend.get("trend_points");
            if (points != null && !points.isEmpty()) {
                sb.append("趋势明细：\n");
                for (Map<String, Object> p : points) {
                    sb.append("  ").append(p.get("date"));
                    sb.append(" 体重 ").append(p.get("weight_kg")).append("kg");
                    if (p.get("bmi") != null) sb.append("，BMI ").append(p.get("bmi"));
                    if (p.get("bmr") != null) sb.append("，BMR ").append(p.get("bmr"));
                    sb.append("\n");
                }
            }
        } else {
            sb.append("⚠️ 近 7 日暂无身体指标记录，请建议用户定期记录体重数据。\n");
        }
        sb.append("\n");

        // 四、今日饮食记录
        List<Map<String, Object>> diet = (List<Map<String, Object>>) snapshot.get("today_diet");
        sb.append("四、今日饮食记录\n");
        if (diet != null && !diet.isEmpty()) {
            for (Map<String, Object> meal : diet) {
                sb.append("餐次：").append(meal.get("meal_type")).append(" ");
                if (meal.get("meal_calories_kcal") != null) {
                    sb.append("（约 ").append(meal.get("meal_calories_kcal")).append(" kcal）");
                }
                sb.append("\n");
                List<Map<String, Object>> items = (List<Map<String, Object>>) meal.get("foods");
                if (items != null) {
                    for (Map<String, Object> item : items) {
                        sb.append("  - ").append(item.get("food_name"));
                        sb.append(" ").append(item.get("eat_weight_g")).append("g");
                        sb.append("：热量 ").append(item.get("calories_kcal")).append(" kcal");
                        sb.append("，蛋白质 ").append(item.get("protein_g")).append(" g");
                        sb.append("，脂肪 ").append(item.get("fat_g")).append(" g");
                        sb.append("，碳水 ").append(item.get("carb_g")).append(" g");
                        if (item.get("gi_value") != null) sb.append("，GI ").append(item.get("gi_value"));
                        sb.append("\n");
                    }
                }
                if (meal.get("remark") != null && !meal.get("remark").toString().trim().isEmpty()) {
                    sb.append("  备注：").append(meal.get("remark")).append("\n");
                }
            }
            Map<String, Object> total = (Map<String, Object>) snapshot.get("today_diet_total");
            if (total != null) {
                sb.append("\n今日营养合计：\n");
                sb.append("  总热量：").append(total.get("total_calories_kcal")).append(" kcal\n");
                sb.append("  蛋白质：").append(total.get("total_protein_g")).append(" g\n");
                sb.append("  脂肪：").append(total.get("total_fat_g")).append(" g\n");
                sb.append("  碳水：").append(total.get("total_carb_g")).append(" g\n");
            }
        } else {
            sb.append("⚠️ 今日暂无饮食记录\n");
        }
        sb.append("\n");

        // 五、近 7 日运动数据
        Map<String, Object> exercise = (Map<String, Object>) snapshot.get("recent_exercise");
        sb.append("五、近 7 日运动数据\n");
        if (exercise != null && exercise.get("note") == null) {
            sb.append("统计区间：").append(exercise.get("date_range")).append("\n");
            sb.append("训练次数：").append(exercise.get("total_sessions")).append(" 次\n");
            sb.append("总时长：").append(exercise.get("total_duration_min")).append(" 分钟\n");
            sb.append("总消耗：").append(exercise.get("total_calories_burned")).append(" kcal\n");
            List<Map<String, Object>> typeBreakdown = (List<Map<String, Object>>) exercise.get("type_breakdown");
            if (typeBreakdown != null && !typeBreakdown.isEmpty()) {
                sb.append("运动类型分布：\n");
                for (Map<String, Object> t : typeBreakdown) {
                    sb.append("  - ").append(t.get("exercise_type"));
                    sb.append("：").append(t.get("sessions")).append(" 次，");
                    sb.append(t.get("duration_min")).append(" 分钟，");
                    sb.append(t.get("calories_burned")).append(" kcal\n");
                }
            }
        } else {
            sb.append("⚠️ 近 7 日暂无运动记录，请建议用户适当增加运动量。\n");
        }
        sb.append("\n");

        // ========== 后端预计算目标值（AI 不得自行计算） ==========
        sb.append("━━━━━━━━━━ 后端预计算目标值（AI 直接引用，禁止重新计算） ━━━━━━━━━━\n");
        Map<String, Object> preCalc = buildPreCalculatedTargets(snapshot);
        sb.append("每日目标热量：").append(preCalc.get("target_calories")).append(" kcal\n");
        sb.append("活动系数：").append(preCalc.get("activity_factor")).append("（").append(preCalc.get("activity_level")).append("）\n");
        sb.append("日均运动消耗：").append(preCalc.get("avg_exercise_calories")).append(" kcal\n");
        sb.append("蛋白质目标：").append(preCalc.get("protein_target_g")).append(" g/天\n");
        sb.append("脂肪目标：").append(preCalc.get("fat_target_g")).append(" g/天\n");
        sb.append("碳水目标：").append(preCalc.get("carb_target_g")).append(" g/天\n");
        sb.append("热量盈亏判断：").append(preCalc.get("calorie_balance")).append("\n\n");

        // ========== RAG 权威参考知识库（可选） ==========
        if (ragKnowledge != null && !ragKnowledge.isEmpty()) {
            sb.append("━━━━━━━━━━ 权威参考知识库（BGE向量检索结果） ━━━━━━━━━━\n");
            sb.append(ragKnowledge).append("\n\n");
            sb.append("注：以上为知识库检索到的权威资料片段，回答时优先依托此资料，资料不足不可编造结论。\n\n");
        }

        // ========== 通用营养参考标准 ==========
        Map<String, Object> dietRef = (Map<String, Object>) snapshot.get("diet_reference");
        if (dietRef != null) {
            sb.append("━━━━━━━━━━ 通用营养参考标准 ━━━━━━━━━━\n");
            Map<String, String> general = (Map<String, String>) dietRef.get("general");
            if (general != null) {
                sb.append("BMI正常范围：").append(general.get("bmi_normal_range")).append("\n");
                sb.append("每日饮水建议：").append(general.get("water_intake")).append("\n");
                sb.append("三餐能量比例：").append(general.get("meal_ratio")).append("\n");
                sb.append("进食建议：").append(general.get("eat_speed")).append("\n");
            }
            Map<String, String> crowdSpecific = (Map<String, String>) dietRef.get("crowd_specific");
            if (crowdSpecific != null) {
                sb.append("人群目标蛋白质：").append(crowdSpecific.get("protein_target")).append("\n");
                sb.append("人群专属饮食建议：").append(crowdSpecific.get("advice")).append("\n");
            }
            Map<String, String> giRef = (Map<String, String>) dietRef.get("gi_reference");
            if (giRef != null) {
                sb.append("GI分级参考：\n");
                sb.append("  低GI（GI<55）：").append(giRef.get("low_gi")).append("\n");
                sb.append("  中GI（GI 55-70）：").append(giRef.get("medium_gi")).append("\n");
                sb.append("  高GI（GI>70）：").append(giRef.get("high_gi")).append("\n");
            }
        }

        return sb.toString();
    }

    /**
     * 后端前置计算：根据 BMR、运动频率、人群类型，预计算每日目标热量和营养素目标。
     * AI 不得自行计算，必须直接引用此结果。
     */
    public Map<String, Object> buildPreCalculatedTargets(Map<String, Object> snapshot) {
        Map<String, Object> preCalc = new LinkedHashMap<>();

        Map<String, Object> metrics = (Map<String, Object>) snapshot.get("today_body_metrics");
        Map<String, Object> exercise = (Map<String, Object>) snapshot.get("recent_exercise");
        Map<String, Object> dietRef = (Map<String, Object>) snapshot.get("diet_reference");
        Map<String, Object> dietTotal = (Map<String, Object>) snapshot.get("today_diet_total");
        Map<String, Object> profile = (Map<String, Object>) snapshot.get("profile");

        // 1. 获取 BMR
        double bmr = 0;
        if (metrics != null && metrics.get("bmr") != null) {
            bmr = ((Number) metrics.get("bmr")).doubleValue();
        } else if (profile != null && profile.get("weight_kg") != null && profile.get("height_cm") != null
                && profile.get("age") != null && profile.get("gender") != null) {
            // 回退计算：Mifflin-St Jeor 公式
            double weight = ((Number) profile.get("weight_kg")).doubleValue();
            double height = ((Number) profile.get("height_cm")).doubleValue();
            int age = ((Number) profile.get("age")).intValue();
            String gender = String.valueOf(profile.get("gender"));
            bmr = 10 * weight + 6.25 * height - 5 * age + ("男".equals(gender) ? 5 : -161);
        }
        preCalc.put("bmr", Math.round(bmr));

        // 2. 根据运动频率确定活动系数
        double activityFactor = 1.2; // 久坐
        String activityLevel = "久坐（无运动）";
        int exerciseSessions = 0;
        double totalExerciseCalories = 0;
        if (exercise != null && exercise.get("total_sessions") != null) {
            exerciseSessions = ((Number) exercise.get("total_sessions")).intValue();
            if (exercise.get("total_calories_burned") != null) {
                totalExerciseCalories = ((Number) exercise.get("total_calories_burned")).doubleValue();
            }
        }
        if (exerciseSessions == 0) {
            activityFactor = 1.2;
            activityLevel = "久坐（无运动）";
        } else if (exerciseSessions <= 2) {
            activityFactor = 1.375;
            activityLevel = "轻度活动（每周1-2次）";
        } else if (exerciseSessions <= 4) {
            activityFactor = 1.55;
            activityLevel = "中度活动（每周3-4次）";
        } else {
            activityFactor = 1.725;
            activityLevel = "高度活动（每周5次以上）";
        }
        preCalc.put("activity_factor", activityFactor);
        preCalc.put("activity_level", activityLevel);

        // 3. 每日目标热量 = BMR × 活动系数
        double targetCalories = bmr * activityFactor;
        preCalc.put("target_calories", Math.round(targetCalories));

        // 4. 日均运动消耗
        double avgExerciseCalories = exerciseSessions > 0 ? totalExerciseCalories / 7.0 : 0;
        preCalc.put("avg_exercise_calories", Math.round(avgExerciseCalories * 10.0) / 10.0);

        // 5. 营养素目标（基于人群推荐）
        String crowdType = profile != null && profile.get("crowdType") != null
                ? String.valueOf(profile.get("crowdType")) : "普通人群";
        double proteinPerKg = 1.0; // g/kg 默认
        if (crowdType != null) {
            if (crowdType.contains("健身")) proteinPerKg = 1.8;
            else if (crowdType.contains("青少年")) proteinPerKg = 1.3;
            else if (crowdType.contains("老年")) proteinPerKg = 1.3;
            else if (crowdType.contains("孕妇")) proteinPerKg = 1.5;
            else if (crowdType.contains("糖尿病")) proteinPerKg = 1.2;
        }
        double weightKg = profile != null && profile.get("weight_kg") != null
                ? ((Number) profile.get("weight_kg")).doubleValue() : 60;
        double proteinTarget = weightKg * proteinPerKg;
        double fatTarget = targetCalories * 0.25 / 9; // 脂肪占25%
        double carbTarget = targetCalories * 0.50 / 4; // 碳水占50%
        preCalc.put("protein_target_g", Math.round(proteinTarget * 10.0) / 10.0);
        preCalc.put("fat_target_g", Math.round(fatTarget * 10.0) / 10.0);
        preCalc.put("carb_target_g", Math.round(carbTarget * 10.0) / 10.0);

        // 6. 热量盈亏判断
        String calorieBalance = "暂无饮食数据，无法判断";
        if (dietTotal != null && dietTotal.get("total_calories_kcal") != null) {
            double todayCalories = ((Number) dietTotal.get("total_calories_kcal")).doubleValue();
            double diff = todayCalories - targetCalories;
            if (diff > 200) {
                calorieBalance = "热量超标 " + Math.round(diff) + " kcal（今日摄入 " + Math.round(todayCalories)
                        + " vs 目标 " + Math.round(targetCalories) + "）";
            } else if (diff < -200) {
                calorieBalance = "热量不足 " + Math.round(-diff) + " kcal（今日摄入 " + Math.round(todayCalories)
                        + " vs 目标 " + Math.round(targetCalories) + "）";
            } else {
                calorieBalance = "热量达标（今日摄入 " + Math.round(todayCalories)
                        + " vs 目标 " + Math.round(targetCalories) + "，差值 " + Math.round(diff) + " kcal）";
            }
        }
        preCalc.put("calorie_balance", calorieBalance);

        return preCalc;
    }
}
