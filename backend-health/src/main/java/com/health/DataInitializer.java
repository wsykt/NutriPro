package com.health;

import com.health.entity.Food;
import com.health.entity.Recipe;
import com.health.entity.RecipeIngredient;
import com.health.entity.User;
import com.health.repository.FoodRepository;
import com.health.repository.RecipeIngredientRepository;
import com.health.repository.RecipeRepository;
import com.health.repository.UserRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.init.ScriptUtils;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import lombok.extern.slf4j.Slf4j;

import java.math.BigDecimal;
import java.security.SecureRandom;
import java.sql.Connection;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Component
public class DataInitializer implements CommandLineRunner {

    private final UserRepository userRepository;
    private final FoodRepository foodRepository;
    private final RecipeRepository recipeRepository;
    private final RecipeIngredientRepository recipeIngredientRepository;
    private final PasswordEncoder passwordEncoder;
    private final JdbcTemplate jdbcTemplate;

    public DataInitializer(UserRepository userRepository, FoodRepository foodRepository,
                           RecipeRepository recipeRepository, RecipeIngredientRepository recipeIngredientRepository,
                           PasswordEncoder passwordEncoder, JdbcTemplate jdbcTemplate) {
        this.userRepository = userRepository;
        this.foodRepository = foodRepository;
        this.recipeRepository = recipeRepository;
        this.recipeIngredientRepository = recipeIngredientRepository;
        this.passwordEncoder = passwordEncoder;
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public void run(String... args) {
        applySchemaOptimizations();
        initAdminUser();
        initDemoUsers();
        initFoods();
        initRecipes();
    }

    /**
     * 执行建表演进脚本（SC-001 起）：补齐 Hibernate 自动建表不生成的索引/约束。
     * 脚本幂等（CREATE INDEX IF NOT EXISTS / CREATE UNIQUE INDEX IF NOT EXISTS），
     * 启动时执行一次，失败仅告警不阻断启动。
     */
    private void applySchemaOptimizations() {
        try (Connection conn = jdbcTemplate.getDataSource().getConnection()) {
            ScriptUtils.executeSqlScript(conn, new ClassPathResource("db/index_optimizations.sql"));
            ScriptUtils.executeSqlScript(conn, new ClassPathResource("db/unique_constraints.sql"));
            log.info("Schema optimizations applied: index_optimizations.sql + unique_constraints.sql");
        } catch (Exception e) {
            log.warn("Schema optimizations skipped ({}), startup continues", e.getMessage());
        }
    }

    private void initAdminUser() {
        // 安全加固：不再内置固定弱口令 admin/admin123。
        // 口令优先级：ADMIN_PASSWORD 环境变量 > 随机生成强口令（打印日志，仅此一次）。
        // 生产模式（设置了 JWT_SECRET）不自动创建 admin，由运维通过 ADMIN_PASSWORD 初始化。
        String adminPassword = System.getenv("ADMIN_PASSWORD");
        boolean prodMode = isEnvNonBlank("JWT_SECRET");
        boolean hasAdminPassword = isEnvNonBlank("ADMIN_PASSWORD");

        if (prodMode && !hasAdminPassword) {
            log.warn("生产模式（检测到 JWT_SECRET）：请通过环境变量 ADMIN_PASSWORD 配置管理员口令，未配置则跳过 admin 自动初始化");
            return;
        }

        String rawPassword = hasAdminPassword ? adminPassword.trim() : generateRandomPassword();
        upsertAdmin(rawPassword, hasAdminPassword);
    }

    /** 创建 admin（不存在时）；若已存在且口令仍是已知默认弱口令 admin123，强制轮换。 */
    private void upsertAdmin(String rawPassword, boolean passwordFromEnv) {
        User admin = userRepository.findByUsername("admin").orElse(null);
        if (admin == null) {
            admin = new User("admin", passwordEncoder.encode(rawPassword));
            admin.setGender("男");
            admin.setHeight(170.0);
            admin.setWeight(65.0);
            admin.setAge(30);
            admin.setCrowdType("普通人");
            admin.setRole("admin");
            userRepository.save(admin);
            log.info("管理员账号 admin 已初始化");
            if (!passwordFromEnv) {
                log.warn("管理员口令未通过 ADMIN_PASSWORD 配置，已生成随机口令：{}（请登录后立即修改，或重启时设置 ADMIN_PASSWORD 环境变量）", rawPassword);
            }
            return;
        }
        if (passwordEncoder.matches("admin123", admin.getPassword())) {
            admin.setPassword(passwordEncoder.encode(rawPassword));
            userRepository.save(admin);
            log.warn("检测到 admin 仍使用已知默认弱口令 admin123，已强制轮换{}", passwordFromEnv ? "" : "，新口令：" + rawPassword);
        }
    }

    private boolean isEnvNonBlank(String name) {
        String value = System.getenv(name);
        return value != null && !value.trim().isEmpty();
    }

    private String generateRandomPassword() {
        final String charset = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%";
        SecureRandom random = new SecureRandom();
        StringBuilder sb = new StringBuilder(16);
        for (int i = 0; i < 16; i++) {
            sb.append(charset.charAt(random.nextInt(charset.length())));
        }
        return sb.toString();
    }

    private void initDemoUsers() {
        createUserIfNotExists("user001", "123456", "男", 168.0, 62.0, 28, "普通人");
        User u2 = createUserIfNotExistsWithReturn("user002", "123456", "女", 162.0, 55.0, 25, "健身");
        if (u2 != null) { u2.setTastePreference("清淡"); u2.setDietaryRestrictions("低脂"); userRepository.save(u2); }
        
        User u3 = createUserIfNotExistsWithReturn("user003", "123456", "男", 172.0, 70.0, 65, "老年");
        if (u3 != null) { u3.setTastePreference("清淡"); u3.setDietaryRestrictions("低盐,低脂"); userRepository.save(u3); }
        
        User u4 = createUserIfNotExistsWithReturn("user004", "123456", "女", 165.0, 60.0, 32, "孕妇");
        if (u4 != null) { u4.setTastePreference("清淡"); u4.setAllergicFoods("海鲜"); userRepository.save(u4); }
        
        createUserIfNotExists("user005", "123456", "男", 175.0, 68.0, 16, "青少年");
        
        User u6 = createUserIfNotExistsWithReturn("user006", "123456", "女", 160.0, 58.0, 45, "糖尿病");
        if (u6 != null) { u6.setTastePreference("清淡"); u6.setDietaryRestrictions("糖尿病,低糖"); u6.setAllergicFoods("花生"); userRepository.save(u6); }
        
        User alice = createUserIfNotExistsWithReturn("alice", "123456", "女", 163.0, 56.0, 30, "普通人");
        if (alice != null) { alice.setTastePreference("清淡"); alice.setAllergicFoods("海鲜"); userRepository.save(alice); }
        
        log.info("Demo users initialized");
    }

    private User createUserIfNotExistsWithReturn(String username, String password, String gender,
                                         Double height, Double weight, Integer age, String crowdType) {
        if (!userRepository.existsByUsername(username)) {
            User user = new User(username, passwordEncoder.encode(password));
            user.setGender(gender);
            user.setHeight(height);
            user.setWeight(weight);
            user.setAge(age);
            user.setCrowdType(crowdType);
            user.setRole("user");
            return user;
        }
        return null;
    }

    private void createUserIfNotExists(String username, String password, String gender,
                                         Double height, Double weight, Integer age, String crowdType) {
        if (!userRepository.existsByUsername(username)) {
            User user = new User(username, passwordEncoder.encode(password));
            user.setGender(gender);
            user.setHeight(height);
            user.setWeight(weight);
            user.setAge(age);
            user.setCrowdType(crowdType);
            user.setRole("user");
            userRepository.save(user);
        }
    }

    private void initFoods() {
        if (foodRepository.count() > 0) {
            return;
        }

        List<Food> foods = Arrays.asList(
            // 主食类 - 米饭面条
            createFood("米饭(熟)", "主食", 130, 2.5, 0.3, 28, 0.4, 73, 7, 0, 5),
            createFood("米饭(生)", "主食", 350, 7, 0.5, 78, 0.4, 83, 7, 0, 3),
            createFood("杂粮饭(熟)", "主食", 116, 3.8, 0.6, 24, 3.2, 48, 22, 0, 22),
            createFood("糙米(生)", "主食", 348, 7.9, 2.7, 75, 3.5, 59, 13, 0, 10),
            createFood("小米(生)", "主食", 361, 9, 3.1, 77, 1.6, 71, 41, 0, 20),
            createFood("小米粥(熟)", "主食", 46, 1.4, 0.3, 10, 0.8, 65, 15, 0, 8),
            createFood("面条(熟)", "主食", 110, 3.3, 0.5, 24, 1.2, 55, 10, 0, 4),
            createFood("面条(生)", "主食", 350, 12, 1.5, 72, 2.4, 80, 15, 0, 15),
            createFood("荞麦面(干生)", "主食", 340, 12.5, 2.2, 70, 6, 40, 45, 0, 32),
            createFood("意面(干生)", "主食", 352, 11, 1.3, 73, 2.5, 58, 18, 0, 16),
            createFood("馒头(白面)", "主食", 223, 7, 1.1, 47, 1.3, 85, 18, 0, 8),
            createFood("全麦馒头", "主食", 205, 9, 2.2, 41, 5, 60, 75, 0, 28),
            createFood("荞麦馒头", "主食", 198, 9.5, 2, 40, 5.8, 55, 82, 0, 33),
            createFood("大饼(白面烙饼)", "主食", 280, 7.5, 6, 48, 1.5, 78, 20, 0, 9),
            createFood("油条", "主食", 380, 6, 17, 50, 0.8, 75, 12, 0, 7),
            createFood("全麦面包", "主食", 250, 10, 3, 45, 6, 69, 80, 0, 30),
            createFood("燕麦片(干生纯燕麦)", "主食", 389, 13, 6.9, 66, 10, 42, 186, 0, 35),
            createFood("红薯(蒸熟)", "主食", 90, 1.6, 0.1, 21, 2.3, 54, 30, 0, 6),
            createFood("土豆(生)", "主食", 77, 2, 0.1, 17, 1.6, 78, 8, 0, 12),
            createFood("蒸土豆(熟)", "主食", 77, 2, 0.1, 17, 1.6, 78, 8, 0, 12),
            createFood("南瓜(生)", "主食", 26, 1, 0.1, 6, 1.6, 75, 16, 0, 9),
            createFood("山药(生)", "主食", 57, 1.9, 0.2, 13, 0.8, 51, 16, 0, 8),
            createFood("蒸山药(熟)", "主食", 72, 2.2, 0.2, 16, 1.1, 54, 22, 0, 10),
            createFood("玉米(煮熟)", "主食", 96, 3.3, 1.4, 19, 2.9, 52, 2, 0, 35),
            createFood("芋头(生)", "主食", 77, 2.2, 0.2, 18, 1.4, 64, 16, 0, 12),

            // 肉蛋类
            createFood("鸡胸肉(生)", "肉蛋类", 133, 31, 1.2, 0, 0, 0, 5, 10, 4),
            createFood("去皮鸡腿肉(生)", "肉蛋类", 165, 26, 6.5, 0, 0, 0, 7, 12, 5),
            createFood("鸭胸肉(去皮生)", "肉蛋类", 105, 23, 1.8, 0, 0, 0, 6, 8, 4),
            createFood("鸡胸丸子(生)", "肉蛋类", 160, 18, 7, 6, 0, 45, 12, 9, 6),
            createFood("瘦牛肉(生)", "肉蛋类", 125, 22, 3.5, 0, 0, 0, 5, 5, 3),
            createFood("瘦羊肉(生)", "肉蛋类", 118, 20, 3.9, 0, 0, 0, 9, 6, 4),
            createFood("瘦猪肉(生)", "肉蛋类", 143, 21, 6, 0, 0, 0, 6, 12, 4),
            createFood("五花肉(生)", "肉蛋类", 395, 13, 37, 0, 0, 0, 4, 3, 2),
            createFood("鸡蛋(全,煮)", "肉蛋类", 144, 13, 10, 1, 0, 0, 50, 30, 47),
            createFood("鸡蛋(全,生)", "肉蛋类", 143, 13, 9.5, 0.7, 0, 0, 48, 29, 45),
            createFood("鸭蛋(水煮)", "肉蛋类", 180, 12, 13, 1.5, 0, 0, 62, 35, 50),
            createFood("鹌鹑蛋(水煮)", "肉蛋类", 160, 12, 11, 1, 0, 0, 64, 32, 55),

            // 水产类
            createFood("三文鱼(生)", "水产", 183, 22, 11, 0, 0, 0, 12, 2000, 25),
            createFood("秋刀鱼(生)", "水产", 140, 20, 6.8, 0, 0, 0, 11, 1300, 22),
            createFood("黄花鱼(大黄鱼,生)", "水产", 100, 18, 3.2, 0, 0, 0, 53, 350, 14),
            createFood("带鱼(生)", "水产", 127, 17, 5.1, 0, 0, 0, 28, 420, 13),
            createFood("龙利鱼(生)", "水产", 77, 18, 0.6, 0, 0, 0, 14, 450, 16),
            createFood("巴沙鱼(生)", "水产", 80, 15, 1.7, 0, 0, 0, 10, 380, 15),
            createFood("鲈鱼(生)", "水产", 105, 18, 3.4, 0, 0, 0, 13, 220, 12),
            createFood("草鱼(生)", "水产", 112, 17, 4.7, 0, 0, 0, 38, 120, 10),
            createFood("沙丁鱼(生)", "水产", 130, 20, 4.8, 0, 0, 0, 180, 1500, 28),
            createFood("虾仁(生)", "水产", 99, 22, 0.8, 0, 0, 0, 54, 30, 2),
            createFood("基围虾(生)", "水产", 93, 20, 1, 0, 0, 0, 46, 28, 3),
            createFood("虾干(干制)", "水产", 280, 55, 3, 0, 0, 0, 900, 60, 5),
            createFood("扇贝(鲜,生)", "水产", 60, 11, 1.1, 2, 0, 0, 142, 180, 10),
            createFood("鱿鱼(鲜生)", "水产", 85, 17, 1.4, 0, 0, 0, 11, 150, 8),
            createFood("鳕鱼(生)", "水产", 82, 20, 0.7, 0, 0, 0, 11, 800, 18),

            // 蔬菜类
            createFood("西兰花(煮)", "蔬菜", 36, 2.6, 0.4, 7, 3.3, 15, 40, 0, 110),
            createFood("菠菜(煮)", "蔬菜", 23, 2.9, 0.4, 3.5, 2.2, 15, 136, 0, 194),
            createFood("胡萝卜(生)", "蔬菜", 35, 0.8, 0.2, 8, 2.8, 39, 32, 0, 14),
            createFood("番茄(生)", "蔬菜", 18, 0.9, 0.2, 4, 1.2, 15, 10, 0, 11),
            createFood("油麦菜(生)", "蔬菜", 15, 1.4, 0.2, 2.5, 1.2, 10, 70, 0, 140),
            createFood("生菜(生)", "蔬菜", 16, 1.3, 0.3, 2.1, 1.1, 12, 34, 0, 73),
            createFood("黄瓜(生)", "蔬菜", 16, 0.7, 0.2, 3, 0.5, 15, 24, 0, 9),
            createFood("冬瓜(生)", "蔬菜", 12, 0.4, 0.2, 2.6, 0.7, 14, 19, 0, 6),
            createFood("芹菜(生茎)", "蔬菜", 16, 0.8, 0.1, 3.9, 1.4, 15, 48, 0, 29),
            createFood("平菇(生)", "蔬菜", 28, 2.1, 0.3, 4.6, 2.3, 18, 11, 0, 32),
            createFood("大白菜(生)", "蔬菜", 17, 1.5, 0.2, 3.2, 1, 23, 45, 0, 80),
            createFood("韭菜(生)", "蔬菜", 25, 2.5, 0.4, 4.5, 1.4, 15, 42, 0, 61),
            createFood("金针菇(生)", "蔬菜", 32, 2.4, 0.4, 6, 2.7, 16, 12, 0, 28),
            createFood("娃娃菜(生)", "蔬菜", 15, 1.3, 0.2, 2.8, 0.9, 22, 33, 0, 75),
            createFood("苦瓜(生)", "蔬菜", 19, 0.9, 0.2, 4, 1.4, 24, 14, 0, 12),
            createFood("茄子(生)", "蔬菜", 25, 1, 0.2, 5, 1.3, 15, 15, 0, 10),

            // 水果类
            createFood("苹果(去皮,生)", "水果", 52, 0.3, 0.2, 14, 2.4, 36, 6, 0, 3),
            createFood("香蕉(生)", "水果", 89, 1.1, 0.2, 23, 2.6, 51, 5, 0, 20),
            createFood("橙子(生)", "水果", 47, 0.9, 0.1, 12, 2.4, 43, 40, 0, 30),
            createFood("猕猴桃(生)", "水果", 61, 1.1, 0.5, 14, 3, 50, 34, 0, 37),
            createFood("草莓(生)", "水果", 32, 0.7, 0.1, 7, 2, 29, 18, 0, 25),
            createFood("葡萄(生)", "水果", 69, 0.6, 0.2, 17, 1.6, 46, 10, 0, 4),
            createFood("梨(生)", "水果", 50, 0.4, 0.2, 13, 2.1, 36, 9, 0, 4),
            createFood("桃子(生)", "水果", 42, 0.6, 0.1, 10, 1.5, 28, 6, 0, 3),

            // 豆制品
            createFood("嫩豆腐", "豆制品", 51, 5, 2.5, 2, 0.3, 42, 350, 0, 15),
            createFood("豆腐皮(干生)", "豆制品", 410, 44, 18, 20, 3.8, 15, 260, 0, 60),
            createFood("黄豆(生)", "豆制品", 390, 36, 16, 34, 15.5, 18, 200, 0, 180),
            createFood("黑豆(生)", "豆制品", 401, 33, 15, 33, 10, 15, 224, 0, 190),
            createFood("纯豆浆", "豆制品", 33, 2.9, 1.6, 1.2, 0.2, 34, 15, 0, 9),

            // 奶类
            createFood("全脂牛奶", "奶类", 61, 3.2, 3.4, 4.8, 0, 27, 120, 2, 5),
            createFood("脱脂牛奶", "奶类", 34, 3.4, 0.1, 5, 0, 27, 125, 1, 5),
            createFood("无糖原味酸奶", "奶类", 70, 4.5, 2.8, 6, 0, 30, 110, 2, 7),

            // 油脂类
            createFood("橄榄油", "油脂类", 884, 0, 100, 0, 0, 0, 1, 0, 0),
            createFood("花生油", "油脂类", 900, 0, 100, 0, 0, 0, 2, 0, 0),
            createFood("玉米油", "油脂类", 900, 0, 100, 0, 0, 0, 1, 0, 0),
            createFood("葵花籽油", "油脂类", 898, 0, 100, 0, 0, 0, 1, 0, 0),
            createFood("山茶油", "油脂类", 882, 0, 100, 0, 0, 0, 2, 0, 0),
            createFood("大豆油", "油脂类", 899, 0, 100, 0, 0, 0, 1, 0, 0),
            createFood("菜籽油", "油脂类", 896, 0, 100, 0, 0, 0, 1, 0, 0),
            createFood("猪油", "油脂类", 897, 0, 100, 0, 0, 0, 0, 0, 0),
            createFood("黄油", "油脂类", 717, 0.8, 81, 0.6, 0, 0, 24, 0, 0),

            // ===== 新增：调味料/加工品（食谱常见食材） =====
            createFood("姜", "蔬菜", 41, 1.3, 0.4, 9, 2, 15, 27, 0, 11),
            createFood("葱", "蔬菜", 32, 1.7, 0.3, 7, 2.1, 20, 29, 0, 16),
            createFood("大蒜", "蔬菜", 126, 4.5, 0.2, 27, 1.1, 15, 38, 0, 3),
            createFood("香菜", "蔬菜", 23, 2.1, 0.5, 3, 1.2, 15, 101, 0, 62),
            createFood("青椒", "蔬菜", 23, 1.1, 0.3, 5, 1.5, 15, 14, 0, 10),
            createFood("彩椒", "蔬菜", 22, 1, 0.2, 5, 1.4, 14, 12, 0, 9),
            createFood("豆芽", "蔬菜", 14, 1.6, 0.1, 3, 2.4, 22, 12, 0, 15),
            createFood("西兰花", "蔬菜", 36, 2.6, 0.4, 7, 3.3, 15, 40, 0, 110),
            createFood("菠菜", "蔬菜", 23, 2.9, 0.4, 3.5, 2.2, 15, 136, 0, 194),

            // 调味料（低热量/无热量类）
            createFood("酱油", "调味料", 56, 8, 0.1, 5, 0, 15, 34, 0, 3),
            createFood("黄酒", "调味料", 66, 1.6, 0, 2, 0, 0, 19, 0, 1),
            createFood("香醋", "调味料", 30, 2.3, 0, 5, 0, 0, 17, 0, 0),
            createFood("食盐", "调味料", 0, 0, 0, 0, 0, 0, 0, 0, 0),
            createFood("白砂糖", "调味料", 387, 0, 0, 100, 0, 65, 1, 0, 0),
            createFood("玉米淀粉", "调味料", 345, 0.4, 0, 86, 0.1, 0, 9, 0, 1),
            createFood("芝麻油", "油脂类", 898, 0, 99.9, 0, 0, 0, 5, 0, 0),
            createFood("花生酱", "调味料", 588, 25, 50, 20, 5.5, 14, 50, 0, 50),
            createFood("豆瓣酱", "调味料", 143, 8, 6, 12, 4.5, 20, 160, 0, 35),
            createFood("番茄酱", "调味料", 83, 1.7, 0.2, 19, 1.2, 15, 14, 0, 5),
            createFood("蚝油", "调味料", 75, 2.5, 0.3, 16, 0, 15, 40, 0, 8),

            // 新增肉蛋类
            createFood("猪小排(生)", "肉蛋类", 264, 18, 21, 0, 0, 0, 14, 8, 5),
            createFood("猪大排(生)", "肉蛋类", 242, 17, 19, 0, 0, 0, 12, 7, 4),
            createFood("牛腩(生)", "肉蛋类", 215, 19, 15, 0, 0, 0, 10, 6, 7),
            createFood("牛腱子(生)", "肉蛋类", 128, 22, 4, 0, 0, 0, 8, 5, 4),
            createFood("鸡腿(生)", "肉蛋类", 181, 20, 11, 0, 0, 0, 12, 5, 6),
            createFood("鸡翅(生)", "肉蛋类", 194, 17, 14, 0, 0, 0, 8, 4, 5),
            createFood("猪蹄(生)", "肉蛋类", 260, 22, 19, 0, 0, 0, 33, 6, 3),
            createFood("猪肝(生)", "肉蛋类", 129, 20, 3.5, 5, 0, 0, 6, 200, 200),
            createFood("鸡肝(生)", "肉蛋类", 118, 17, 4.5, 2, 0, 0, 10, 300, 588),
            createFood("猪肚(生)", "肉蛋类", 110, 16, 4.5, 0.5, 0, 0, 8, 5, 8),
            createFood("猪油(熬)", "油脂类", 897, 0, 100, 0, 0, 0, 0, 0, 0),
            createFood("黄油(无盐)", "油脂类", 717, 0.8, 81, 0.6, 0, 0, 24, 0, 0),

            // 新增水产
            createFood("蛤蜊(生)", "水产", 62, 10, 1.5, 2, 0, 0, 133, 120, 16),
            createFood("生蚝(生)", "水产", 61, 7, 1.8, 3, 0, 0, 35, 200, 20),
            createFood("海带(生)", "水产", 12, 1.2, 0.1, 2, 0.5, 15, 168, 50, 50),
            createFood("紫菜(干)", "水产", 250, 26, 3.5, 45, 22, 15, 440, 100, 200),

            // 新增水果
            createFood("西瓜(生)", "水果", 30, 0.6, 0.2, 7, 0.4, 72, 7, 0, 3),
            createFood("蓝莓(生)", "水果", 57, 0.7, 0.3, 14, 3.6, 34, 6, 0, 6),
            createFood("芒果(生)", "水果", 60, 0.8, 0.4, 15, 1.6, 51, 11, 0, 14),
            createFood("火龙果(生)", "水果", 55, 1.1, 0.4, 13, 1.8, 25, 8, 0, 5),
            createFood("柠檬(生)", "水果", 29, 1.1, 0.3, 9, 2.8, 15, 26, 0, 11),

            // 新增豆制品
            createFood("毛豆(生)", "豆制品", 131, 11.5, 5, 10, 4.5, 15, 65, 0, 80),
            createFood("腐竹(干)", "豆制品", 459, 45, 22, 23, 1.5, 15, 87, 0, 50),
            createFood("千张(白)", "豆制品", 155, 15, 8, 5, 1, 15, 120, 0, 20),

            // 新增主食
            createFood("面粉(标准粉)", "主食", 350, 11, 1.5, 73, 2.5, 80, 30, 0, 20),
            createFood("糯米(生)", "主食", 350, 7, 1, 79, 0.8, 82, 8, 0, 12),
            createFood("紫米(生)", "主食", 340, 8, 1.5, 74, 3.2, 50, 16, 0, 18),
            createFood("薏米(生)", "主食", 352, 12, 2, 69, 4.8, 40, 42, 0, 25),
            createFood("绿豆(生)", "主食", 329, 22, 0.8, 60, 16, 27, 110, 0, 200),
            createFood("红豆(生)", "主食", 324, 20, 0.5, 61, 12, 28, 80, 0, 190),
            createFood("全麦粉", "主食", 335, 14, 3, 70, 10, 55, 40, 0, 38),
            createFood("饺子皮(生)", "主食", 240, 7, 1, 50, 0.5, 75, 15, 0, 8),
            createFood("馄饨皮(生)", "主食", 230, 7, 0.8, 48, 0.3, 70, 12, 0, 6),

            // 新增：干货/菌菇
            createFood("干香菇", "蔬菜", 260, 18, 2.5, 50, 32, 20, 80, 0, 100),
            createFood("木耳(干)", "蔬菜", 200, 10, 1.5, 40, 30, 15, 250, 0, 50),
            createFood("银耳(干)", "蔬菜", 200, 5, 1, 40, 30, 15, 30, 0, 6),
            createFood("枸杞(干)", "水果", 350, 14, 1.5, 77, 15, 40, 60, 0, 50),
            createFood("红枣(干)", "水果", 276, 3, 0.5, 66, 6, 45, 64, 0, 25),
            createFood("花生仁(生)", "水果", 563, 25, 48, 16, 8, 14, 70, 0, 80),
            createFood("核桃(干)", "水果", 650, 15, 65, 14, 6, 15, 95, 0, 50),
            createFood("腰果(生)", "水果", 553, 18, 44, 27, 3, 15, 40, 0, 30),
            createFood("杏仁(生)", "水果", 578, 21, 50, 20, 11, 10, 250, 0, 30)
        );

        foodRepository.saveAll(foods);
        log.info("Initialized {} food items", foods.size());
    }

    private static final Map<String, int[]> CATEGORY_VISIBILITY = new HashMap<String, int[]>();
    static {
        CATEGORY_VISIBILITY.put("主食", new int[]{1, 1, 0});
        CATEGORY_VISIBILITY.put("肉蛋类", new int[]{0, 0, 0});
        CATEGORY_VISIBILITY.put("水产", new int[]{0, 1, 1});
        CATEGORY_VISIBILITY.put("蔬菜", new int[]{1, 1, 0});
        CATEGORY_VISIBILITY.put("水果", new int[]{1, 0, 0});
        CATEGORY_VISIBILITY.put("豆制品", new int[]{1, 1, 0});
        CATEGORY_VISIBILITY.put("奶类", new int[]{1, 0, 0});
        CATEGORY_VISIBILITY.put("油脂类", new int[]{0, 0, 0});
        CATEGORY_VISIBILITY.put("零食", new int[]{1, 0, 0});
    }

    private Food createFood(String name, String category, int calorie, double protein,
                            double fat, double carb, double dietFiber, double giValue,
                            double calcium, double dha, double folicAcid) {
        Food food = new Food();
        food.setFoodName(name);
        food.setFoodCategory(category);
        food.setCalorie(BigDecimal.valueOf(calorie));
        food.setProtein(BigDecimal.valueOf(protein));
        food.setFat(BigDecimal.valueOf(fat));
        food.setCarb(BigDecimal.valueOf(carb));
        food.setDietFiber(BigDecimal.valueOf(dietFiber));
        food.setGiValue(BigDecimal.valueOf(giValue));
        food.setCalcium(BigDecimal.valueOf(calcium));
        food.setDha(BigDecimal.valueOf(dha));
        food.setFolicAcid(BigDecimal.valueOf(folicAcid));
        food.setStatus("approved");
        int[] vis = CATEGORY_VISIBILITY.get(category);
        if (vis != null) {
            food.setShowGi(vis[0]);
            food.setShowFolicAcid(vis[1]);
            food.setShowDha(vis[2]);
        } else {
            food.setShowGi(0);
            food.setShowFolicAcid(0);
            food.setShowDha(0);
        }
        return food;
    }

    private void initRecipes() {
        if (recipeRepository.count() > 0) {
            return;
        }

        // ===== 已有食谱（保留并更新标签）=====
        Recipe r2 = createRecipe("清蒸鲈鱼", "鲜嫩多汁的清蒸鲈鱼，DHA丰富，适合孕期食用", 180, 28, 6, 3, 0.5, "水产,清淡,高蛋白,孕妇,低GI");
        Recipe r3 = createRecipe("蒜蓉西兰花", "健康美味的蒜蓉西兰花，高纤维低热量", 80, 5, 4, 8, 3, "蔬菜,清淡,减脂,低GI,均衡");
        Recipe r4 = createRecipe("番茄炒蛋", "简单又美味的家常快手菜，营养均衡", 150, 12, 10, 8, 1, "家常菜,清淡,均衡,青少年");
        Recipe r5 = createRecipe("宫保鸡丁", "香辣可口的宫保鸡丁，高蛋白", 280, 22, 18, 15, 1.5, "肉类,微辣,均衡,青少年");
        Recipe r6 = createRecipe("清炒虾仁", "清爽嫩滑的清炒虾仁，低脂高蛋白", 160, 25, 5, 6, 0.5, "水产,清淡,高蛋白,减脂,健身");
        Recipe r7 = createRecipe("麻婆豆腐", "麻辣鲜香的经典川菜，植物蛋白丰富", 220, 15, 15, 8, 1, "豆制品,微辣,均衡");
        Recipe r8 = createRecipe("糖醋排骨", "酸甜可口的糖醋排骨", 320, 20, 25, 15, 0.5, "肉类,家常,青少年");
        Recipe r9 = createRecipe("凉拌黄瓜", "清爽开胃的凉拌黄瓜，零脂低卡", 40, 1, 2, 5, 1, "蔬菜,清淡,减脂,低GI,高血压");
        Recipe r10 = createRecipe("白灼菜心", "清淡健康的白灼菜心", 60, 3, 2, 7, 2, "蔬菜,清淡,减脂,高血压,均衡");
        Recipe r11 = createRecipe("冬瓜排骨汤", "清淡滋补的冬瓜排骨汤，低脂少盐", 120, 15, 4, 10, 1.5, "汤品,清淡,老年人,均衡,高血压");
        Recipe r12 = createRecipe("虾仁豆腐羹", "营养丰富的虾仁豆腐羹，易消化", 100, 12, 5, 8, 0.5, "汤品,清淡,高蛋白,老年人,孕妇");

        // ===== 新增健康食谱 =====
        // DHA/孕妇
        Recipe r13 = createRecipe("清蒸三文鱼", "DHA丰富，Omega-3优质脂肪，适合孕期补充", 185, 22, 11, 2, 0, "水产,清淡,高蛋白,孕妇,DHA");
        // 孕妇/补铁
        Recipe r14 = createRecipe("菠菜猪肝汤", "补铁补叶酸，适合孕期及贫血人群", 65, 8, 2, 4, 1.5, "汤品,清淡,孕妇,均衡");
        // 糖尿病/低GI
        Recipe r15 = createRecipe("苦瓜炒蛋", "低GI健康菜，适合控糖饮食", 70, 5, 3.5, 4, 1, "蔬菜,清淡,低GI,糖尿病,减脂");
        // 低GI/糖尿病/老年人
        Recipe r16 = createRecipe("燕麦牛奶粥", "低GI早餐，膳食纤维丰富，适合控糖和老年人", 105, 5, 1.5, 18, 4, "主食,清淡,低GI,老年人,糖尿病,减脂");
        // 青少年/均衡
        Recipe r17 = createRecipe("番茄炖牛腩", "酸甜开胃的高蛋白炖菜，适合青少年成长", 140, 12, 9, 5, 0.5, "肉类,清淡,高蛋白,青少年,均衡");
        // 减脂/健身
        Recipe r18 = createRecipe("鸡胸肉沙拉", "低脂高蛋白，健身减脂首选", 75, 9, 3, 3, 1, "蔬菜,清淡,减脂,健身,高蛋白");
        // 老年人/高蛋白
        Recipe r19 = createRecipe("蒸蛋羹", "软嫩易消化，适合老年人和孕期", 150, 13, 10, 1, 0, "家常菜,清淡,老年人,孕妇,高蛋白");
        // 低GI/糖尿病/老年人
        Recipe r20 = createRecipe("小米南瓜粥", "养胃低GI粥品，适合老年人和控糖人群", 55, 1.5, 0.5, 12, 1.5, "主食,清淡,老年人,低GI,糖尿病,均衡");
        // 健身/高蛋白
        Recipe r21 = createRecipe("卤牛肉", "高蛋白低脂肪，健身人群理想选择", 160, 25, 4, 1, 0, "肉类,清淡,健身,高蛋白,减脂");
        // 减脂/低GI
        Recipe r22 = createRecipe("什锦蔬菜汤", "多种蔬菜搭配，零脂低卡高纤维", 25, 1.5, 0.3, 5, 2, "汤品,清淡,减脂,均衡,低GI");
        // 减脂/高蛋白
        Recipe r23 = createRecipe("水煮虾", "原味鲜甜，零脂肪高蛋白", 70, 15, 0.5, 0, 0, "水产,清淡,减脂,健身,高蛋白,孕妇");
        // 低GI/减脂/高血压
        Recipe r24 = createRecipe("凉拌木耳", "清脆爽口，膳食纤维丰富，有益血管健康", 55, 2, 2, 10, 5, "蔬菜,清淡,低GI,减脂,高血压");
        // 减脂/均衡
        Recipe r25 = createRecipe("番茄豆腐汤", "清淡低卡，植物蛋白丰富", 35, 3, 1, 4, 0.5, "汤品,清淡,减脂,均衡,低GI,老年人");
        // 健身/高蛋白
        Recipe r26 = createRecipe("菌菇炒鸡胸", "菌菇提鲜，高蛋白低脂肪", 95, 18, 2, 3, 1.5, "肉类,清淡,健身,高蛋白,减脂,低GI");

        recipeRepository.save(r2);
        recipeRepository.save(r3);
        recipeRepository.save(r4);
        recipeRepository.save(r5);
        recipeRepository.save(r6);
        recipeRepository.save(r7);
        recipeRepository.save(r8);
        recipeRepository.save(r9);
        recipeRepository.save(r10);
        recipeRepository.save(r11);
        recipeRepository.save(r12);
        recipeRepository.save(r13);
        recipeRepository.save(r14);
        recipeRepository.save(r15);
        recipeRepository.save(r16);
        recipeRepository.save(r17);
        recipeRepository.save(r18);
        recipeRepository.save(r19);
        recipeRepository.save(r20);
        recipeRepository.save(r21);
        recipeRepository.save(r22);
        recipeRepository.save(r23);
        recipeRepository.save(r24);
        recipeRepository.save(r25);
        recipeRepository.save(r26);

        addIngredients(r2, new String[][]{{"鲈鱼", "1", "条"}, {"姜片", "10", "g"}, {"葱段", "20", "g"}, {"蒸鱼豉油", "30", "ml"}, {"食用油", "20", "ml"}});
        addIngredients(r3, new String[][]{{"西兰花", "300", "g"}, {"蒜蓉", "20", "g"}, {"盐", "3", "g"}, {"食用油", "15", "ml"}});
        addIngredients(r4, new String[][]{{"番茄", "2", "个"}, {"鸡蛋", "3", "个"}, {"盐", "3", "g"}, {"食用油", "20", "ml"}, {"葱花", "10", "g"}});
        addIngredients(r5, new String[][]{{"鸡胸肉", "300", "g"}, {"花生米", "50", "g"}, {"干辣椒", "10", "g"}, {"花椒", "5", "g"}, {"生抽", "20", "ml"}, {"料酒", "10", "ml"}});
        addIngredients(r6, new String[][]{{"虾仁", "200", "g"}, {"西兰花", "100", "g"}, {"胡萝卜", "50", "g"}, {"盐", "3", "g"}, {"食用油", "15", "ml"}});
        addIngredients(r7, new String[][]{{"嫩豆腐", "300", "g"}, {"肉末", "100", "g"}, {"郫县豆瓣酱", "20", "g"}, {"花椒粉", "5", "g"}, {"葱花", "10", "g"}});
        addIngredients(r8, new String[][]{{"排骨", "500", "g"}, {"姜片", "10", "g"}, {"葱段", "20", "g"}, {"生抽", "30", "ml"}, {"香醋", "20", "ml"}, {"冰糖", "40", "g"}});
        addIngredients(r9, new String[][]{{"黄瓜", "2", "根"}, {"蒜末", "15", "g"}, {"生抽", "20", "ml"}, {"香醋", "10", "ml"}, {"香油", "5", "ml"}, {"盐", "2", "g"}});
        addIngredients(r10, new String[][]{{"菜心", "300", "g"}, {"姜片", "5", "g"}, {"生抽", "20", "ml"}, {"食用油", "10", "ml"}});
        addIngredients(r11, new String[][]{{"排骨", "300", "g"}, {"冬瓜", "400", "g"}, {"姜片", "10", "g"}, {"盐", "3", "g"}, {"葱花", "10", "g"}});
        addIngredients(r12, new String[][]{{"虾仁", "150", "g"}, {"嫩豆腐", "200", "g"}, {"鸡蛋", "1", "个"}, {"盐", "3", "g"}, {"葱花", "10", "g"}});

        // 新食谱食材
        addIngredients(r13, new String[][]{{"三文鱼", "200", "g"}, {"姜片", "10", "g"}, {"葱段", "20", "g"}, {"蒸鱼豉油", "20", "ml"}});
        addIngredients(r14, new String[][]{{"菠菜", "200", "g"}, {"猪肝", "100", "g"}, {"姜片", "5", "g"}, {"盐", "3", "g"}});
        addIngredients(r15, new String[][]{{"苦瓜", "200", "g"}, {"鸡蛋", "2", "个"}, {"盐", "3", "g"}, {"花生油", "10", "ml"}});
        addIngredients(r16, new String[][]{{"燕麦片", "50", "g"}, {"脱脂牛奶", "200", "ml"}});
        addIngredients(r17, new String[][]{{"牛腩", "300", "g"}, {"番茄", "2", "个"}, {"姜片", "10", "g"}, {"盐", "3", "g"}, {"葱段", "10", "g"}});
        addIngredients(r18, new String[][]{{"鸡胸肉", "150", "g"}, {"生菜", "100", "g"}, {"番茄", "100", "g"}, {"黄瓜", "100", "g"}, {"橄榄油", "10", "ml"}, {"香醋", "10", "ml"}});
        addIngredients(r19, new String[][]{{"鸡蛋", "2", "个"}, {"盐", "2", "g"}, {"葱花", "5", "g"}});
        addIngredients(r20, new String[][]{{"小米", "50", "g"}, {"南瓜", "100", "g"}});
        addIngredients(r21, new String[][]{{"牛腱子", "300", "g"}, {"生抽", "20", "ml"}, {"姜片", "10", "g"}, {"葱段", "20", "g"}});
        addIngredients(r22, new String[][]{{"冬瓜", "100", "g"}, {"胡萝卜", "50", "g"}, {"娃娃菜", "100", "g"}, {"金针菇", "50", "g"}, {"盐", "3", "g"}});
        addIngredients(r23, new String[][]{{"虾仁", "200", "g"}, {"姜片", "10", "g"}, {"料酒", "10", "ml"}});
        addIngredients(r24, new String[][]{{"木耳", "30", "g"}, {"蒜末", "10", "g"}, {"香醋", "10", "ml"}, {"生抽", "10", "ml"}, {"香油", "5", "ml"}});
        addIngredients(r25, new String[][]{{"番茄", "1", "个"}, {"嫩豆腐", "200", "g"}, {"盐", "3", "g"}, {"葱花", "10", "g"}});
        addIngredients(r26, new String[][]{{"鸡胸肉", "150", "g"}, {"平菇", "150", "g"}, {"盐", "3", "g"}, {"花生油", "10", "ml"}, {"生抽", "10", "ml"}});

        log.info("Initialized 25 recipes (removed 红烧肉, added 14 healthy recipes)");
    }

    private Recipe createRecipe(String name, String desc, int calories, double protein,
                                double fat, double carbs, double fiber, String tags) {
        Recipe recipe = new Recipe();
        recipe.setRecipeName(name);
        recipe.setDescription(desc);
        recipe.setCalories(BigDecimal.valueOf(calories));
        recipe.setProtein(BigDecimal.valueOf(protein));
        recipe.setFat(BigDecimal.valueOf(fat));
        recipe.setCarbs(BigDecimal.valueOf(carbs));
        recipe.setFiber(BigDecimal.valueOf(fiber));
        recipe.setTags(tags);
        recipe.setSource("system");
        return recipe;
    }

    private void addIngredients(Recipe recipe, String[][] ingredients) {
        for (String[] ing : ingredients) {
            RecipeIngredient ri = new RecipeIngredient();
            ri.setRecipeId(recipe.getRecipeId());
            ri.setIngredientName(ing[0]);
            ri.setAmount(BigDecimal.valueOf(Double.parseDouble(ing[1])));
            ri.setUnit(ing[2]);
            recipeIngredientRepository.save(ri);
        }
    }
}
