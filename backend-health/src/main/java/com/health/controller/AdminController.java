package com.health.controller;

import com.health.dto.ApiResponse;
import com.health.entity.Article;
import com.health.entity.ArticleAnalysis;
import com.health.entity.Comment;
import com.health.entity.ExerciseRecord;
import com.health.entity.FamilyRelation;
import com.health.entity.Food;
import com.health.entity.Post;
import com.health.entity.Recipe;
import com.health.entity.User;
import com.health.service.ArticleAnalysisService;
import com.health.service.ArticleService;
import com.health.service.CommunityService;
import com.health.service.ExerciseRecordService;
import com.health.service.FamilyRelationService;
import com.health.service.FoodService;
import com.health.service.ProfileService;
import com.health.service.RecipeService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/admin")
@PreAuthorize("hasRole('ADMIN')")
public class AdminController {

    private final ProfileService profileService;
    private final FoodService foodService;
    private final FamilyRelationService relationService;
    private final ExerciseRecordService exerciseRecordService;
    private final CommunityService communityService;
    private final RecipeService recipeService;
    private final ArticleService articleService;
    private final ArticleAnalysisService articleAnalysisService;

    public AdminController(ProfileService profileService, FoodService foodService, FamilyRelationService relationService,
                           ExerciseRecordService exerciseRecordService, CommunityService communityService, RecipeService recipeService,
                           ArticleService articleService, ArticleAnalysisService articleAnalysisService) {
        this.profileService = profileService;
        this.foodService = foodService;
        this.relationService = relationService;
        this.exerciseRecordService = exerciseRecordService;
        this.communityService = communityService;
        this.recipeService = recipeService;
        this.articleService = articleService;
        this.articleAnalysisService = articleAnalysisService;
    }

    @GetMapping("/users")
    public ResponseEntity<ApiResponse<List<Map<String, Object>>>> getAllUsers() {
        List<User> users = profileService.getAllUsers();
        // 脱敏：不返回 password 哈希，仅返回业务字段
        List<Map<String, Object>> result = users.stream().map(u -> {
            Map<String, Object> map = new LinkedHashMap<>();
            map.put("userId", u.getUserId());
            map.put("username", u.getUsername());
            map.put("gender", u.getGender());
            map.put("height", u.getHeight());
            map.put("weight", u.getWeight());
            map.put("age", u.getAge());
            map.put("crowdType", u.getCrowdType());
            map.put("role", u.getRole());
            map.put("createdAt", u.getCreatedAt() != null ? u.getCreatedAt().toString() : null);
            map.put("allergicFoods", u.getAllergicFoods());
            map.put("dietaryRestrictions", u.getDietaryRestrictions());
            map.put("tastePreference", u.getTastePreference());
            map.put("elderlyMode", u.getElderlyMode());
            return map;
        }).collect(Collectors.toList());
        return ResponseEntity.ok(ApiResponse.success(result));
    }

    @GetMapping("/users-with-relations")
    public ResponseEntity<ApiResponse<List<Map<String, Object>>>> getAllUsersWithRelations() {
        List<User> users = profileService.getAllUsers();
        List<Map<String, Object>> result = users.stream().map(u -> {
            Map<String, Object> map = new LinkedHashMap<>();
            map.put("userId", u.getUserId());
            map.put("username", u.getUsername());
            map.put("crowdType", u.getCrowdType());
            map.put("role", u.getRole());
            map.put("age", u.getAge());
            map.put("gender", u.getGender());

            List<FamilyRelation> myWards = relationService.getMyWards(u.getUserId());
            List<FamilyRelation> myGuardians = relationService.getMyGuardians(u.getUserId());

            List<String> wardNames = myWards.stream()
                .map(r -> r.getWardUsername() != null ? r.getWardUsername() : "id-" + r.getWardId())
                .collect(Collectors.toList());
            List<String> guardianNames = myGuardians.stream()
                .map(r -> r.getGuardianUsername() != null ? r.getGuardianUsername() : "id-" + r.getGuardianId())
                .collect(Collectors.toList());

            map.put("wards", wardNames);
            map.put("guardians", guardianNames);
            return map;
        }).collect(Collectors.toList());
        return ResponseEntity.ok(ApiResponse.success(result));
    }

    @GetMapping("/users/{userId}")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getUserDetail(@PathVariable Integer userId) {
        Map<String, Object> info = profileService.getUserInfo(userId);
        if (info == null) {
            return ResponseEntity.badRequest().body(ApiResponse.error("用户不存在"));
        }
        return ResponseEntity.ok(ApiResponse.success(info));
    }

    @DeleteMapping("/users/{userId}")
    public ResponseEntity<ApiResponse<String>> deleteUser(@PathVariable Integer userId) {
        try {
            Map<String, Object> info = profileService.getUserInfo(userId);
            if (info == null) {
                return ResponseEntity.badRequest().body(ApiResponse.error("用户不存在"));
            }
            if ("admin".equals(info.get("role"))) {
                return ResponseEntity.badRequest().body(ApiResponse.error("不能删除管理员账号"));
            }
            profileService.deleteUser(userId);
            return ResponseEntity.ok(ApiResponse.success("用户已删除", "deleted"));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }

    @GetMapping("/food/list")
    public ResponseEntity<ApiResponse<List<Food>>> getAllFoods() {
        List<Food> foods = foodService.getAllFoods();
        return ResponseEntity.ok(ApiResponse.success(foods));
    }

    @PutMapping("/food/update/{foodId}")
    public ResponseEntity<ApiResponse<Food>> updateFood(@PathVariable Integer foodId, @RequestBody Food updated) {
        try {
            Food food = foodService.updateFood(foodId, updated);
            return ResponseEntity.ok(ApiResponse.success("食物已更新", food));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }

    @DeleteMapping("/food/{foodId}")
    public ResponseEntity<ApiResponse<String>> deleteFood(@PathVariable Integer foodId) {
        try {
            foodService.deleteFood(foodId);
            return ResponseEntity.ok(ApiResponse.success("食物已删除", "deleted"));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }

    @PostMapping("/food/approve/{foodId}")
    public ResponseEntity<ApiResponse<Food>> approveFood(@PathVariable Integer foodId) {
        try {
            Food approved = foodService.approveFood(foodId);
            return ResponseEntity.ok(ApiResponse.success("食物已审核通过", approved));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }

    @PostMapping("/food/reject/{foodId}")
    public ResponseEntity<ApiResponse<Food>> rejectFood(@PathVariable Integer foodId) {
        try {
            Food rejected = foodService.rejectFood(foodId);
            return ResponseEntity.ok(ApiResponse.success("食物已拒绝", rejected));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(e.getMessage()));
        }
    }

    @GetMapping("/stats/crowd-type")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getCrowdTypeStats() {
        List<User> users = profileService.getAllUsers();
        Map<String, Long> counts = users.stream()
            .filter(u -> u.getRole() == null || !"admin".equals(u.getRole()))
            .collect(Collectors.groupingBy(u -> {
                String ct = u.getCrowdType();
                return (ct == null || ct.trim().isEmpty()) ? "未设置" : ct;
            }, Collectors.counting()));

        List<Map<String, Object>> list = new ArrayList<>();
        for (Map.Entry<String, Long> entry : counts.entrySet()) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("name", entry.getKey());
            item.put("value", entry.getValue().intValue());
            list.add(item);
        }
        list.sort((a, b) -> Integer.compare((Integer) b.get("value"), (Integer) a.get("value")));

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("total", users.size());
        result.put("data", list);
        return ResponseEntity.ok(ApiResponse.success(result));
    }

    // ===================== 运动记录管理 =====================
    @GetMapping("/exercise-records")
    public ResponseEntity<ApiResponse<List<ExerciseRecord>>> getAllExerciseRecords() {
        List<ExerciseRecord> records = exerciseRecordService.getAllRecords();
        return ResponseEntity.ok(ApiResponse.success(records));
    }

    @GetMapping("/exercise-records/status/{status}")
    public ResponseEntity<ApiResponse<List<ExerciseRecord>>> getExerciseRecordsByStatus(@PathVariable String status) {
        List<ExerciseRecord> records = exerciseRecordService.getRecordsByStatus(status);
        return ResponseEntity.ok(ApiResponse.success(records));
    }

    @PostMapping("/exercise-records/approve/{recordId}")
    public ResponseEntity<ApiResponse<ExerciseRecord>> approveExerciseRecord(@PathVariable Integer recordId) {
        ExerciseRecord record = exerciseRecordService.approveRecord(recordId);
        if (record == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(ApiResponse.success("已审核通过", record));
    }

    @PostMapping("/exercise-records/reject/{recordId}")
    public ResponseEntity<ApiResponse<ExerciseRecord>> rejectExerciseRecord(@PathVariable Integer recordId) {
        ExerciseRecord record = exerciseRecordService.rejectRecord(recordId);
        if (record == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(ApiResponse.success("已拒绝", record));
    }

    @DeleteMapping("/exercise-records/{recordId}")
    public ResponseEntity<ApiResponse<String>> deleteExerciseRecord(@PathVariable Integer recordId) {
        exerciseRecordService.deleteRecordById(recordId);
        return ResponseEntity.ok(ApiResponse.success("已删除", "deleted"));
    }

    // ===================== 食谱库管理 =====================
    @GetMapping("/recipes")
    public ResponseEntity<ApiResponse<List<Recipe>>> getAllRecipes() {
        List<Recipe> recipes = recipeService.getAllRecipes();
        return ResponseEntity.ok(ApiResponse.success(recipes));
    }

    @GetMapping("/recipes/{recipeId}")
    public ResponseEntity<ApiResponse<Recipe>> getRecipeById(@PathVariable Integer recipeId) {
        Recipe recipe = recipeService.getRecipeById(recipeId);
        if (recipe == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(ApiResponse.success(recipe));
    }

    @PostMapping("/recipes")
    public ResponseEntity<ApiResponse<Recipe>> createRecipe(@RequestBody Map<String, Object> recipeData) {
        Recipe recipe = recipeService.saveRecipe(0, recipeData);
        return ResponseEntity.ok(ApiResponse.success("创建成功", recipe));
    }

    @PutMapping("/recipes/{recipeId}")
    public ResponseEntity<ApiResponse<Recipe>> updateRecipe(@PathVariable Integer recipeId, @RequestBody Map<String, Object> recipeData) {
        Recipe recipe = recipeService.updateRecipe(recipeId, recipeData);
        if (recipe == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(ApiResponse.success("更新成功", recipe));
    }

    @DeleteMapping("/recipes/{recipeId}")
    public ResponseEntity<ApiResponse<String>> deleteRecipe(@PathVariable Integer recipeId) {
        recipeService.deleteRecipe(recipeId);
        return ResponseEntity.ok(ApiResponse.success("已删除", "deleted"));
    }

    // ===================== 动态管理 =====================
    @GetMapping("/posts")
    public ResponseEntity<ApiResponse<List<Post>>> getAllPosts() {
        List<Post> posts = communityService.getAllPostsForAdmin();
        return ResponseEntity.ok(ApiResponse.success(posts));
    }

    @GetMapping("/posts/status/{status}")
    public ResponseEntity<ApiResponse<List<Post>>> getPostsByStatus(@PathVariable String status) {
        List<Post> posts = communityService.getPostsByStatus(status);
        return ResponseEntity.ok(ApiResponse.success(posts));
    }

    @PostMapping("/posts/approve/{postId}")
    public ResponseEntity<ApiResponse<Post>> approvePost(@PathVariable Integer postId) {
        Post post = communityService.approvePost(postId);
        if (post == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(ApiResponse.success("已审核通过", post));
    }

    @PostMapping("/posts/reject/{postId}")
    public ResponseEntity<ApiResponse<Post>> rejectPost(@PathVariable Integer postId) {
        Post post = communityService.rejectPost(postId);
        if (post == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(ApiResponse.success("已拒绝", post));
    }

    @DeleteMapping("/posts/{postId}")
    public ResponseEntity<ApiResponse<String>> deletePost(@PathVariable Integer postId) {
        communityService.deletePost(postId);
        return ResponseEntity.ok(ApiResponse.success("已删除", "deleted"));
    }

    @GetMapping("/comments")
    public ResponseEntity<ApiResponse<List<Comment>>> getAllComments() {
        List<Comment> comments = communityService.getAllCommentsForAdmin();
        return ResponseEntity.ok(ApiResponse.success(comments));
    }

    @GetMapping("/comments/status/{status}")
    public ResponseEntity<ApiResponse<List<Comment>>> getCommentsByStatus(@PathVariable String status) {
        List<Comment> comments = communityService.getCommentsByStatus(status);
        return ResponseEntity.ok(ApiResponse.success(comments));
    }

    @PostMapping("/comments/approve/{commentId}")
    public ResponseEntity<ApiResponse<Comment>> approveComment(@PathVariable Integer commentId) {
        Comment comment = communityService.approveComment(commentId);
        if (comment == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(ApiResponse.success("已审核通过", comment));
    }

    @PostMapping("/comments/reject/{commentId}")
    public ResponseEntity<ApiResponse<Comment>> rejectComment(@PathVariable Integer commentId) {
        Comment comment = communityService.rejectComment(commentId);
        if (comment == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(ApiResponse.success("已拒绝", comment));
    }

    @DeleteMapping("/comments/{commentId}")
    public ResponseEntity<ApiResponse<String>> deleteComment(@PathVariable Integer commentId) {
        communityService.deleteComment(commentId);
        return ResponseEntity.ok(ApiResponse.success("已删除", "deleted"));
    }

    // ===================== 文章管理（含AI质量分析） =====================

    /** 获取所有文章（含质量评分） */
    @GetMapping("/articles")
    public ResponseEntity<ApiResponse<List<Article>>> getAllArticles() {
        List<Article> articles = articleService.getAllArticlesForAdmin();
        return ResponseEntity.ok(ApiResponse.success(articles));
    }

    /** 获取单篇文章详情 */
    @GetMapping("/articles/{id}")
    public ResponseEntity<ApiResponse<Article>> getArticleDetail(@PathVariable Integer id) {
        Article article = articleService.getArticleByIdDirect(id);
        if (article == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(ApiResponse.success(article));
    }

    /** 更新文章 */
    @PutMapping("/articles/{id}")
    public ResponseEntity<ApiResponse<Article>> updateArticle(@PathVariable Integer id, @RequestBody Article article) {
        Article updated = articleService.updateArticle(id, article);
        if (updated == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(ApiResponse.success("文章已更新", updated));
    }

    /** 删除文章 */
    @DeleteMapping("/articles/{id}")
    public ResponseEntity<ApiResponse<String>> deleteArticle(@PathVariable Integer id) {
        articleService.deleteArticle(id);
        return ResponseEntity.ok(ApiResponse.success("文章已删除", "deleted"));
    }

    /** 执行AI文章质量分析 */
    @PostMapping("/articles/{id}/analyze")
    public ResponseEntity<ApiResponse<ArticleAnalysis>> analyzeArticle(@PathVariable Integer id) {
        ArticleAnalysis analysis = articleAnalysisService.analyzeArticle(id);
        if (analysis == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(ApiResponse.success("分析完成", analysis));
    }

    /** 批量分析所有文章 */
    @PostMapping("/articles/analyze-all")
    public ResponseEntity<ApiResponse<Map<String, Object>>> analyzeAllArticles() {
        int count = articleAnalysisService.analyzeAllArticles();
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("analyzedCount", count);
        return ResponseEntity.ok(ApiResponse.success("已分析 " + count + " 篇文章", result));
    }

    /** 获取文章的最新分析记录 */
    @GetMapping("/articles/{id}/analysis")
    public ResponseEntity<ApiResponse<ArticleAnalysis>> getLatestAnalysis(@PathVariable Integer id) {
        ArticleAnalysis analysis = articleAnalysisService.getLatestAnalysis(id);
        if (analysis == null) {
            return ResponseEntity.ok(ApiResponse.success(null));
        }
        return ResponseEntity.ok(ApiResponse.success(analysis));
    }

    /** 获取文章的所有分析历史 */
    @GetMapping("/articles/{id}/analysis-history")
    public ResponseEntity<ApiResponse<List<ArticleAnalysis>>> getAnalysisHistory(@PathVariable Integer id) {
        List<ArticleAnalysis> history = articleAnalysisService.getAnalysisHistory(id);
        return ResponseEntity.ok(ApiResponse.success(history));
    }

    /** 获取低质量文章列表 */
    @GetMapping("/articles/low-quality")
    public ResponseEntity<ApiResponse<List<Map<String, Object>>>> getLowQualityArticles(
            @RequestParam(defaultValue = "60") int threshold) {
        List<Map<String, Object>> articles = articleAnalysisService.getLowQualityArticles(threshold);
        return ResponseEntity.ok(ApiResponse.success(articles));
    }

    /** 获取分析统计数据 */
    @GetMapping("/articles/analysis-stats")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getAnalysisStats() {
        Map<String, Object> stats = articleAnalysisService.getAnalysisStats();
        return ResponseEntity.ok(ApiResponse.success(stats));
    }

    /** 应用优化建议 */
    @PostMapping("/articles/analysis/{id}/apply")
    public ResponseEntity<ApiResponse<ArticleAnalysis>> applyOptimization(@PathVariable Long id) {
        ArticleAnalysis analysis = articleAnalysisService.applyOptimization(id);
        if (analysis == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(ApiResponse.success("优化建议已应用", analysis));
    }
}
