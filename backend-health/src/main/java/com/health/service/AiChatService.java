package com.health.service;

import com.health.entity.*;
import com.health.repository.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.*;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.*;

@Service
public class AiChatService {

    private static final String AI_SERVICE_URL = "http://localhost:8002/api/v1";
    private static final int CONNECT_TIMEOUT = 5000;   // 连接超时 5秒
    private static final int READ_TIMEOUT = 30000;     // 读取超时 30秒
    private static final int CIRCUIT_BREAKER_THRESHOLD = 3;  // 连续失败3次后熔断
    private static final int CIRCUIT_BREAKER_RESET_MS = 60000; // 60秒后尝试恢复

    // 简单断路器状态
    private int consecutiveFailures = 0;
    private long circuitOpenUntil = 0;

    public Map<String, Object> parseVoice(Integer userId, String text) {
        try {
            Map<String, Object> requestBody = new LinkedHashMap<>();
            requestBody.put("text", text);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            ResponseEntity<String> response = restTemplate.postForEntity(
                    AI_SERVICE_URL + "/voice/parse", entity, String.class);

            if (response.getBody() == null) {
                throw new RuntimeException("AI 服务返回空响应");
            }

            return objectMapper.readValue(response.getBody(), Map.class);
        } catch (Exception e) {
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", "语音解析失败: " + e.getMessage());
            return errorMap;
        }
    }

    public Map<String, Object> analyzeNutrition(Integer userId) {
        User user = userRepository.findById(userId).orElse(null);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }

        String today = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);
        Map<String, Object> snapshot = buildHealthSnapshot(user, today);

        try {
            Map<String, Object> requestBody = new LinkedHashMap<>();
            requestBody.put("user_profile", snapshot.get("profile"));
            requestBody.put("daily_nutrition", snapshot.get("today_diet_total"));
            requestBody.put("daily_exercise", new LinkedHashMap<>());

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            ResponseEntity<String> response = restTemplate.postForEntity(
                    AI_SERVICE_URL + "/nutrition/analyze", entity, String.class);

            if (response.getBody() == null) {
                throw new RuntimeException("AI 服务返回空响应");
            }

            return objectMapper.readValue(response.getBody(), Map.class);
        } catch (Exception e) {
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", "营养分析失败: " + e.getMessage());
            return errorMap;
        }
    }

    public Map<String, Object> auditFood(Map<String, Object> foodData) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(foodData), headers);

            ResponseEntity<String> response = restTemplate.postForEntity(
                    AI_SERVICE_URL + "/food/audit", entity, String.class);

            if (response.getBody() == null) {
                throw new RuntimeException("AI 服务返回空响应");
            }

            return objectMapper.readValue(response.getBody(), Map.class);
        } catch (Exception e) {
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", "食物审核失败: " + e.getMessage());
            return errorMap;
        }
    }

    public Map<String, Object> generateWeeklyReport(Integer userId) {
        User user = userRepository.findById(userId).orElse(null);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }

        try {
            Map<String, Object> requestBody = new LinkedHashMap<>();
            Map<String, Object> userProfile = new LinkedHashMap<>();
            userProfile.put("username", user.getUsername());
            userProfile.put("gender", user.getGender());
            userProfile.put("age", user.getAge());
            userProfile.put("height", user.getHeight());
            userProfile.put("weight", user.getWeight());
            userProfile.put("crowd_type", user.getCrowdType());
            requestBody.put("user_profile", userProfile);
            requestBody.put("weekly_stats", new LinkedHashMap<>());

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            ResponseEntity<String> response = restTemplate.postForEntity(
                    AI_SERVICE_URL + "/report/weekly-summary", entity, String.class);

            if (response.getBody() == null) {
                throw new RuntimeException("AI 服务返回空响应");
            }

            return objectMapper.readValue(response.getBody(), Map.class);
        } catch (Exception e) {
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", "周报生成失败: " + e.getMessage());
            return errorMap;
        }
    }

    public Map<String, Object> generateArticle(String topic, String targetCrowd) {
        try {
            Map<String, Object> requestBody = new LinkedHashMap<>();
            requestBody.put("topic", topic);
            requestBody.put("target_crowd", targetCrowd);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            ResponseEntity<String> response = restTemplate.postForEntity(
                    AI_SERVICE_URL + "/article/generate", entity, String.class);

            if (response.getBody() == null) {
                throw new RuntimeException("AI 服务返回空响应");
            }

            return objectMapper.readValue(response.getBody(), Map.class);
        } catch (Exception e) {
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", "文章生成失败: " + e.getMessage());
            return errorMap;
        }
    }

    public Map<String, Object> generateDietPlan(Integer userId, String goal) {
        User user = userRepository.findById(userId).orElse(null);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }

        try {
            Map<String, Object> requestBody = new LinkedHashMap<>();
            Map<String, Object> userProfile = new LinkedHashMap<>();
            userProfile.put("username", user.getUsername());
            userProfile.put("gender", user.getGender());
            userProfile.put("age", user.getAge());
            userProfile.put("height", user.getHeight());
            userProfile.put("weight", user.getWeight());
            userProfile.put("crowd_type", user.getCrowdType());
            requestBody.put("user_profile", userProfile);
            requestBody.put("goal", goal);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            ResponseEntity<String> response = restTemplate.postForEntity(
                    AI_SERVICE_URL + "/diet/plan", entity, String.class);

            if (response.getBody() == null) {
                throw new RuntimeException("AI 服务返回空响应");
            }

            return objectMapper.readValue(response.getBody(), Map.class);
        } catch (Exception e) {
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", "膳食计划生成失败: " + e.getMessage());
            return errorMap;
        }
    }

    public Map<String, Object> recommendRecipe(Map<String, Object> body) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(body), headers);

            ResponseEntity<String> response = restTemplate.postForEntity(
                    AI_SERVICE_URL + "/food/recommend", entity, String.class);

            if (response.getBody() == null) {
                throw new RuntimeException("AI 服务返回空响应");
            }

            return objectMapper.readValue(response.getBody(), Map.class);
        } catch (Exception e) {
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", "菜谱推荐失败: " + e.getMessage());
            return errorMap;
        }
    }

    public Map<String, Object> adviseExercise(Integer userId, Map<String, Object> body) {
        User user = userRepository.findById(userId).orElse(null);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }

        try {
            Map<String, Object> requestBody = new LinkedHashMap<>();

            Map<String, Object> userProfile = new LinkedHashMap<>();
            userProfile.put("username", user.getUsername());
            userProfile.put("gender", user.getGender());
            userProfile.put("age", user.getAge());
            userProfile.put("height", user.getHeight());
            userProfile.put("weight", user.getWeight());
            userProfile.put("crowd_type", user.getCrowdType());
            if (user.getDietaryRestrictions() != null) {
                userProfile.put("dietary_restrictions", user.getDietaryRestrictions());
            }
            requestBody.put("user_profile", userProfile);
            requestBody.put("goal", body.getOrDefault("goal", "保持健康"));
            requestBody.put("preferences", body.getOrDefault("preferences", ""));
            requestBody.put("chronic_diseases", body.getOrDefault("chronic_diseases", new ArrayList<>()));

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            ResponseEntity<String> response = restTemplate.postForEntity(
                    AI_SERVICE_URL + "/exercise/advice", entity, String.class);

            if (response.getBody() == null) {
                throw new RuntimeException("AI 服务返回空响应");
            }

            return objectMapper.readValue(response.getBody(), Map.class);
        } catch (Exception e) {
            Map<String, Object> errorMap = new LinkedHashMap<>();
            errorMap.put("error", "运动建议生成失败: " + e.getMessage());
            return errorMap;
        }
    }

    private final UserRepository userRepository;
    private final BodyMetricsHistoryRepository historyRepository;
    private final DietMealRepository dietMealRepository;
    private final DietItemRepository dietItemRepository;
    private final FoodRepository foodRepository;
    private final AiConversationRecordRepository recordRepository;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    public AiChatService(UserRepository userRepository,
                         BodyMetricsHistoryRepository historyRepository,
                         DietMealRepository dietMealRepository,
                         DietItemRepository dietItemRepository,
                         FoodRepository foodRepository,
                         AiConversationRecordRepository recordRepository) {
        this.userRepository = userRepository;
        this.historyRepository = historyRepository;
        this.dietMealRepository = dietMealRepository;
        this.dietItemRepository = dietItemRepository;
        this.foodRepository = foodRepository;
        this.recordRepository = recordRepository;
        this.objectMapper = new ObjectMapper();

        // 配置 RestTemplate 超时
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(CONNECT_TIMEOUT);
        factory.setReadTimeout(READ_TIMEOUT);
        this.restTemplate = new RestTemplate(factory);
    }

    /**
     * 检查断路器状态，熔断时返回提示
     */
    private String checkCircuitBreaker() {
        if (consecutiveFailures >= CIRCUIT_BREAKER_THRESHOLD) {
            if (System.currentTimeMillis() < circuitOpenUntil) {
                return "⚠️ AI 服务暂时熔断保护中（连续失败 " + consecutiveFailures + " 次），"
                        + "请等待 " + ((circuitOpenUntil - System.currentTimeMillis()) / 1000) + " 秒后重试。";
            } else {
                // 恢复期：半开状态
                consecutiveFailures = 0;
                circuitOpenUntil = 0;
            }
        }
        return null;
    }

    private void onAiServiceSuccess() {
        consecutiveFailures = 0;
        circuitOpenUntil = 0;
    }

    private void onAiServiceFailure() {
        consecutiveFailures++;
        if (consecutiveFailures >= CIRCUIT_BREAKER_THRESHOLD) {
            circuitOpenUntil = System.currentTimeMillis() + CIRCUIT_BREAKER_RESET_MS;
        }
    }

    @Transactional
    public Map<String, Object> consult(Integer userId, String question) {
        User user = userRepository.findById(userId).orElse(null);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }

        String today = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);

        // 1. 构建健康数据快照
        Map<String, Object> snapshot = buildHealthSnapshot(user, today);
        String snapshotJson;
        try {
            snapshotJson = objectMapper.writeValueAsString(snapshot);
        } catch (Exception e) {
            snapshotJson = "{}";
        }

        // 2. 调用 AI 服务
        String reply = callAiService(userId, question, snapshot);

        // 3. 保存记录
        AiConversationRecord record = new AiConversationRecord();
        record.setUserId(userId);
        record.setModel("AI_SERVICE");
        record.setQuestion(question);
        record.setReply(reply);
        record.setHealthSnapshotJson(snapshotJson);
        record = recordRepository.save(record);

        // 4. 返回结果
        Map<String, Object> result = new HashMap<>();
        result.put("recordId", record.getId());
        result.put("reply", reply);
        result.put("forUserId", userId);
        result.put("forUsername", user.getUsername());
        result.put("snapshot", snapshot);
        return result;
    }

    /**
     * 构建用户健康数据快照：用户资料 + 今日身体指标 + 今日饮食记录
     */
    private Map<String, Object> buildHealthSnapshot(User user, String date) {
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
            List<DietItem> dietItems = dietItemRepository.findByMealId(meal.getMealId());

            for (DietItem item : dietItems) {
                Food food = foodRepository.findById(item.getFoodId()).orElse(null);
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

        // 系统健康饮食参考
        snapshot.put("diet_reference", buildDietReference(user.getCrowdType()));

        return snapshot;
    }

    /**
     * 系统健康饮食参考知识（按人群类型给出参考标准）
     */
    private Map<String, Object> buildDietReference(String crowdType) {
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
        if ("健身人群".equals(crowdType)) {
            crowdSpecific.put("protein_target", "1.6 - 2.2 g/kg 体重/天");
            crowdSpecific.put("advice", "高蛋白、适量碳水、健康脂肪。训练后30分钟内补充蛋白质20-30g。");
        } else if ("青少年".equals(crowdType)) {
            crowdSpecific.put("protein_target", "1.2 - 1.5 g/kg 体重/天");
            crowdSpecific.put("advice", "足够热量和蛋白质，足量钙和维生素D，规律三餐。");
        } else if ("老年人".equals(crowdType)) {
            crowdSpecific.put("protein_target", "1.2 - 1.4 g/kg 体重/天");
            crowdSpecific.put("advice", "高蛋白、充足钙与维生素D，少食多餐，低盐低油。");
        } else if ("孕妇".equals(crowdType)) {
            crowdSpecific.put("protein_target", "1.3 - 1.6 g/kg 体重/天");
            crowdSpecific.put("advice", "足量叶酸、钙、铁、DHA；避免生冷、生的肉蛋类；禁酒。");
        } else if ("糖尿病患者".equals(crowdType)) {
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
     * 构建发给 DeepSeek 的系统提示词
     */
    private String buildSystemPrompt(User user, Map<String, Object> snapshot) {
        StringBuilder sb = new StringBuilder();
        sb.append("你是一个专业的健康咨询助手。请基于以下用户健康数据，用中文给出实用的健康建议。\n\n");

        // 用户资料
        Map<String, Object> profile = (Map<String, Object>) snapshot.get("profile");
        sb.append("【用户基本资料】\n");
        sb.append("用户名：").append(profile.get("username")).append("\n");
        sb.append("性别：").append(profile.get("gender")).append("\n");
        sb.append("年龄：").append(profile.get("age")).append("\n");
        sb.append("身高：").append(profile.get("height_cm")).append(" cm\n");
        sb.append("体重：").append(profile.get("weight_kg")).append(" kg\n");
        sb.append("BMI：").append(profile.get("bmi")).append("\n");
        sb.append("人群类型：").append(profile.get("crowdType")).append("\n\n");

        // 今日身体指标
        Map<String, Object> metrics = (Map<String, Object>) snapshot.get("today_body_metrics");
        sb.append("【今日身体指标快照】\n");
        sb.append("日期：").append(snapshot.get("date")).append("\n");
        sb.append("身高：").append(metrics.get("height_cm")).append(" cm\n");
        sb.append("体重：").append(metrics.get("weight_kg")).append(" kg\n");
        if (metrics.get("bmi") != null) sb.append("BMI：").append(metrics.get("bmi")).append("\n");
        if (metrics.get("bmr") != null) sb.append("基础代谢(BMR)：").append(metrics.get("bmr")).append(" kcal\n");
        sb.append("\n");

        // 今日饮食记录
        List<Map<String, Object>> diet = (List<Map<String, Object>>) snapshot.get("today_diet");
        if (diet != null && !diet.isEmpty()) {
            sb.append("【今日饮食记录】\n");
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
                sb.append("  热量：").append(total.get("total_calories_kcal")).append(" kcal\n");
                sb.append("  蛋白质：").append(total.get("total_protein_g")).append(" g\n");
                sb.append("  脂肪：").append(total.get("total_fat_g")).append(" g\n");
                sb.append("  碳水：").append(total.get("total_carb_g")).append(" g\n");
            }
        } else {
            sb.append("【今日饮食记录】暂无数据\n");
        }
        sb.append("\n");

        // 饮食参考知识
        Map<String, Object> dietRef = (Map<String, Object>) snapshot.get("diet_reference");
        if (dietRef != null) {
            Map<String, String> general = (Map<String, String>) dietRef.get("general");
            if (general != null) {
                sb.append("【健康参考知识】\n");
                sb.append("BMI正常范围：").append(general.get("bmi_normal_range")).append("\n");
                sb.append("每日饮水建议：").append(general.get("water_intake")).append("\n");
                sb.append("三餐比例：").append(general.get("meal_ratio")).append("\n");
            }
            Map<String, String> crowdSpecific = (Map<String, String>) dietRef.get("crowd_specific");
            if (crowdSpecific != null) {
                sb.append("蛋白质推荐：").append(crowdSpecific.get("protein_target")).append("\n");
                sb.append("建议：").append(crowdSpecific.get("advice")).append("\n");
            }
            Map<String, String> giRef = (Map<String, String>) dietRef.get("gi_reference");
            if (giRef != null) {
                sb.append("低GI食物：").append(giRef.get("low_gi")).append("\n");
            }
        }

        sb.append("\n【输出要求】\n");
        sb.append("1. 基于上述用户数据，给出具体、实用的建议\n");
        sb.append("2. 如涉及严重健康问题，请提醒用户咨询专业医生\n");
        sb.append("3. 用中文回答，条理清晰，300字以内\n");

        return sb.toString();
    }

    /**
     * 调用 AI 服务编排层生成食谱（走 Agent 编排层，享受知识库检索+记忆+降级）
     */
    public String callRecipeApi(String systemPrompt, String userQuestion) {
        try {
            Map<String, Object> requestBody = new LinkedHashMap<>();
            requestBody.put("message", systemPrompt + "\n\n" + userQuestion);
            requestBody.put("user_id", 0);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            ResponseEntity<String> response = restTemplate.postForEntity(
                    AI_SERVICE_URL + "/chat", entity, String.class);

            if (response.getBody() == null) {
                throw new RuntimeException("AI 服务返回空响应");
            }

            Map<String, Object> responseMap = objectMapper.readValue(response.getBody(), Map.class);
            String content = (String) responseMap.get("response");
            return content != null ? content : "未返回有效内容";

        } catch (Exception e) {
            throw new RuntimeException("调用AI服务生成食谱失败: " + e.getMessage(), e);
        }
    }

    private String callAiService(Integer userId, String question, Map<String, Object> healthSnapshot) {
        // 断路器检查
        String breakerMsg = checkCircuitBreaker();
        if (breakerMsg != null) {
            return breakerMsg;
        }

        try {
            Map<String, Object> requestBody = new LinkedHashMap<>();
            requestBody.put("message", question);
            requestBody.put("user_id", userId);
            requestBody.put("health_snapshot", healthSnapshot);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            ResponseEntity<String> response = restTemplate.postForEntity(
                    AI_SERVICE_URL + "/chat", entity, String.class);

            if (response.getBody() == null) {
                onAiServiceFailure();
                throw new RuntimeException("AI 服务返回空响应");
            }

            Map<String, Object> responseMap = objectMapper.readValue(response.getBody(), Map.class);
            String reply = (String) responseMap.get("response");
            onAiServiceSuccess();
            return reply != null ? reply : "未返回有效内容";

        } catch (Exception e) {
            onAiServiceFailure();
            String errorMsg = e.getMessage();
            if (errorMsg != null && errorMsg.contains("Connection refused")) {
                return "⚠️ AI 服务未启动，请先启动 Python AI 服务（端口 8002）。";
            }
            if (errorMsg != null && errorMsg.contains("timeout")) {
                return "⚠️ AI 服务响应超时，请稍后重试。";
            }
            return "⚠️ AI 回复失败：" + (errorMsg != null ? errorMsg : "未知错误")
                    + "\n\n如问题持续，请检查 AI 服务是否正常运行。";
        }
    }
}
