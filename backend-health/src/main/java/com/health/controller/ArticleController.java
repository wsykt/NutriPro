package com.health.controller;

import com.health.entity.Article;
import com.health.service.ArticleService;
import com.health.service.AsyncArticleTaskService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.net.InetAddress;
import java.net.URI;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/articles")
@Slf4j
public class ArticleController {

    @Autowired
    private ArticleService articleService;

    @Autowired
    private AsyncArticleTaskService asyncArticleTaskService;

    @GetMapping
    public ResponseEntity<List<Article>> getAllArticles(
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String audience) {
        if ((category != null && !category.isEmpty()) || (audience != null && !audience.isEmpty())) {
            return ResponseEntity.ok(articleService.getArticlesByFilter(category, audience));
        }
        return ResponseEntity.ok(articleService.getAllArticlesForAdmin());
    }

    @GetMapping("/latest")
    public ResponseEntity<List<Article>> getLatestArticles(@RequestParam(defaultValue = "10") int limit) {
        return ResponseEntity.ok(articleService.getLatestArticles(limit));
    }

    @GetMapping("/{id}")
    public ResponseEntity<Article> getArticleById(@PathVariable Integer id) {
        Article article = articleService.getArticleByIdWithView(id);
        return article != null ? ResponseEntity.ok(article) : ResponseEntity.notFound().build();
    }

    @GetMapping("/category/{category}")
    public ResponseEntity<List<Article>> getArticlesByCategory(@PathVariable String category) {
        return ResponseEntity.ok(articleService.getArticlesByCategory(category));
    }

    @GetMapping("/topic/{topic}")
    public ResponseEntity<List<Article>> getArticlesByTopic(@PathVariable String topic) {
        return ResponseEntity.ok(articleService.getArticlesByTopic(topic));
    }

    @GetMapping("/search")
    public ResponseEntity<List<Article>> searchArticles(@RequestParam String keyword) {
        return ResponseEntity.ok(articleService.searchArticles(keyword));
    }

    @GetMapping("/top/views")
    public ResponseEntity<List<Article>> getTopByViews() {
        return ResponseEntity.ok(articleService.getTopByViews());
    }

    @GetMapping("/top/likes")
    public ResponseEntity<List<Article>> getTopByLikes() {
        return ResponseEntity.ok(articleService.getTopByLikes());
    }

    @GetMapping("/categories")
    public ResponseEntity<List<String>> getAllCategories() {
        return ResponseEntity.ok(articleService.getAllCategories());
    }

    @GetMapping("/topics")
    public ResponseEntity<List<String>> getAllTopics() {
        return ResponseEntity.ok(articleService.getAllTopics());
    }

    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Article> createArticle(@RequestBody Article article) {
        return ResponseEntity.ok(articleService.createArticle(article));
    }

    @PutMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Article> updateArticle(@PathVariable Integer id, @RequestBody Article article) {
        Article updated = articleService.updateArticle(id, article);
        return updated != null ? ResponseEntity.ok(updated) : ResponseEntity.notFound().build();
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Void> deleteArticle(@PathVariable Integer id) {
        articleService.deleteArticle(id);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/{id}/like")
    public ResponseEntity<Article> likeArticle(@PathVariable Integer id) {
        Article updated = articleService.likeArticle(id);
        return updated != null ? ResponseEntity.ok(updated) : ResponseEntity.notFound().build();
    }

    /**
     * AI 生成科普文章：主题 + 人群 → 母稿 → 拆分三版 → 校验 → 入库。
     * 返回三篇文章和质量评分。
     */
    @PostMapping("/generate")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> generateArticle(@RequestBody Map<String, String> request) {
        String topic = request.get("topic");
        String persona = request.get("persona");
        if (persona == null || persona.trim().isEmpty()) {
            persona = request.getOrDefault("target_crowd", "普通人群");
        }

        if (topic == null || topic.trim().isEmpty()) {
            Map<String, Object> err = new LinkedHashMap<String, Object>();
            err.put("code", 400);
            err.put("message", "主题不能为空");
            return ResponseEntity.badRequest().body(err);
        }

        try {
            Map<String, Object> result = articleService.generateAndSave(topic.trim(), persona);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            Map<String, Object> err = new LinkedHashMap<String, Object>();
            err.put("code", 500);
            err.put("message", "生成失败：" + e.getMessage());
            return ResponseEntity.internalServerError().body(err);
        }
    }

    /**
     * 外部母稿导入：pipeline 双模型流水线生成的母稿 → 复用后端拆分逻辑 → 三版入库。
     * 请求体：{"motherDraft": "母稿全文", "topic": "孕妇叶酸补充", "persona": "孕妇"}
     */
    @PostMapping("/import-mother")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> importMotherDraft(@RequestBody Map<String, String> request) {
        String motherDraft = request != null ? request.get("motherDraft") : null;
        String topic = request != null ? request.get("topic") : null;
        String persona = request != null ? request.get("persona") : null;

        if (motherDraft == null || motherDraft.trim().isEmpty()) {
            Map<String, Object> err = new LinkedHashMap<String, Object>();
            err.put("code", 400);
            err.put("message", "母稿内容不能为空");
            return ResponseEntity.badRequest().body(err);
        }

        try {
            Map<String, Object> result = articleService.importMotherDraft(motherDraft, topic, persona);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            Map<String, Object> err = new LinkedHashMap<String, Object>();
            err.put("code", 500);
            err.put("message", "母稿导入失败：" + e.getMessage());
            return ResponseEntity.internalServerError().body(err);
        }
    }

    /** 获取同主题不同篇幅的相关文章（排除当前文章） */
    @GetMapping("/related/{topicGroupId}")
    public ResponseEntity<List<Article>> getRelatedArticles(
            @PathVariable String topicGroupId,
            @RequestParam(required = false) Integer excludeId) {
        return ResponseEntity.ok(articleService.getRelatedArticles(topicGroupId, excludeId));
    }

    /** 按主题分组ID获取三版文章 */
    @GetMapping("/topic-group/{topicGroupId}")
    public ResponseEntity<List<Article>> getByTopicGroup(@PathVariable String topicGroupId) {
        return ResponseEntity.ok(articleService.getArticlesByTopicGroup(topicGroupId));
    }

    /**
     * 清空所有文章并重建 Demo 数据（5 主题 × 3 篇幅 = 15 篇）。
     * 仅管理员可调用。
     */
    @PostMapping("/reset-demo")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> resetDemoArticles() {
        try {
            Map<String, Object> result = articleService.resetDemoArticles();
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            Map<String, Object> err = new LinkedHashMap<String, Object>();
            err.put("code", 500);
            err.put("message", "重置失败：" + e.getMessage());
            return ResponseEntity.internalServerError().body(err);
        }
    }

    /**
     * 自纠错进化：针对单篇文章，取其质量分析问题 → 注入提示词 → 重新生成。
     * 闭环流程：AI分析 → 识别问题 → 生成建议 → 存储结果 → 管理员审核 → 应用优化 → 持续迭代
     */
    @PostMapping("/regenerate-with-correction/{articleId}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> regenerateWithCorrection(@PathVariable Integer articleId) {
        try {
            Map<String, Object> result = articleService.regenerateWithCorrection(articleId);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            Map<String, Object> err = new LinkedHashMap<String, Object>();
            err.put("code", 500);
            err.put("message", "自纠错重新生成失败：" + e.getMessage());
            return ResponseEntity.internalServerError().body(err);
        }
    }

    /**
     * 知识库自学习：管理员手动向向量知识库写入文档。
     * 支持提交官方文档、科研文章等权威资料。
     */
    @PostMapping("/knowledge/ingest")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> ingestKnowledgeDocument(@RequestBody Map<String, Object> body) {
        String content = body != null ? String.valueOf(body.getOrDefault("content", "")) : "";
        String source = body != null ? String.valueOf(body.getOrDefault("source", "手动提交")) : "手动提交";
        String category = body != null ? String.valueOf(body.getOrDefault("category", "science_article")) : "science_article";
        String targetCrowd = body != null ? String.valueOf(body.getOrDefault("target_crowd", "")) : "";

        if (content.trim().isEmpty()) {
            Map<String, Object> err = new LinkedHashMap<String, Object>();
            err.put("code", 400);
            err.put("message", "content 不能为空");
            return ResponseEntity.badRequest().body(err);
        }

        try {
            Map<String, Object> result = articleService.ingestKnowledgeDocument(content, source, category, targetCrowd);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            Map<String, Object> err = new LinkedHashMap<String, Object>();
            err.put("code", 500);
            err.put("message", "知识库写入失败：" + e.getMessage());
            return ResponseEntity.internalServerError().body(err);
        }
    }

    /**
     * 知识库自学习：查询知识库文档列表。
     */
    @GetMapping("/knowledge/list")
    public ResponseEntity<Map<String, Object>> listKnowledgeDocuments(
            @RequestParam(name = "limit", defaultValue = "50") int limit) {
        try {
            Map<String, Object> result = articleService.listKnowledgeDocuments(limit);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            Map<String, Object> err = new LinkedHashMap<String, Object>();
            err.put("code", 500);
            err.put("message", "查询失败：" + e.getMessage());
            return ResponseEntity.internalServerError().body(err);
        }
    }

    /**
     * 知识库自学习：联网获取权威资料并入库。
     * 支持两种模式：主题搜索 / URL直接抓取。
     *
     * 请求体示例（主题搜索）：
     * {"topic": "糖尿病饮食原则", "target_crowd": "糖尿病", "max_results": 3}
     *
     * 请求体示例（URL抓取）：
     * {"urls": ["https://...", "https://..."], "target_crowd": "糖尿病"}
     */
    @PostMapping("/knowledge/acquire")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> acquireKnowledge(@RequestBody Map<String, Object> body) {
        String topic = body != null ? String.valueOf(body.getOrDefault("topic", "")) : "";
        String targetCrowd = body != null ? String.valueOf(body.getOrDefault("target_crowd", "")) : "";
        int maxResults = 3;
        if (body != null && body.get("max_results") != null) {
            try {
                maxResults = Integer.parseInt(String.valueOf(body.get("max_results")));
            } catch (NumberFormatException e) {
                log.debug("max_results 参数解析失败，使用默认值 {}: {}", maxResults, e.getMessage());
            }
        }

        @SuppressWarnings("unchecked")
        java.util.List<String> urls = body != null ? (java.util.List<String>) body.get("urls") : null;

        if (topic.trim().isEmpty() && (urls == null || urls.isEmpty())) {
            Map<String, Object> err = new LinkedHashMap<String, Object>();
            err.put("code", 400);
            err.put("message", "请提供 topic 或 urls");
            return ResponseEntity.badRequest().body(err);
        }

        // SSRF 防护：仅允许 http/https 协议且目标不是内网/回环地址
        if (urls != null && !urls.isEmpty()) {
            for (String url : urls) {
                if (!isSafeFetchUrl(url)) {
                    Map<String, Object> err = new LinkedHashMap<String, Object>();
                    err.put("code", 400);
                    err.put("message", "URL 不合法或指向内网地址，禁止抓取：" + url);
                    return ResponseEntity.badRequest().body(err);
                }
            }
        }

        try {
            Map<String, Object> result = articleService.acquireKnowledge(
                    topic.trim().isEmpty() ? null : topic,
                    urls,
                    maxResults,
                    targetCrowd);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            Map<String, Object> err = new LinkedHashMap<String, Object>();
            err.put("code", 500);
            err.put("message", "知识获取失败：" + e.getMessage());
            return ResponseEntity.internalServerError().body(err);
        }
    }

    /**
     * RAG 素材热度统计：帮助管理员识别知识缺口，定向补充文档。
     */
    @GetMapping("/knowledge/hot-stat")
    public ResponseEntity<Map<String, Object>> getRagHotStats() {
        try {
            Map<String, Object> result = articleService.getRagHotStats();
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            Map<String, Object> err = new LinkedHashMap<String, Object>();
            err.put("code", 500);
            err.put("message", "查询失败：" + e.getMessage());
            return ResponseEntity.internalServerError().body(err);
        }
    }

    /**
     * 方案C：混合架构生成科普文章（RAG + 多Agent）。
     *
     * 工作流：前置RAG检索 → 资料搜集Agent → 撰写母稿 → 事实校验Agent → 失败重试 → 拆分入库 → 素材沉淀
     *
     * 支持模式切换：
     * - mode=rag（默认）：纯RAG模式（方案A），调用 /generate
     * - mode=hybrid：混合架构模式（方案C），调用 /generate-hybrid
     */
    @PostMapping("/generate-hybrid")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> generateHybrid(@RequestBody Map<String, Object> body) {
        String topic = body != null ? String.valueOf(body.getOrDefault("topic", "")).trim() : "";
        String persona = body != null ? String.valueOf(body.getOrDefault("target_crowd", "普通人群")).trim() : "普通人群";

        if (topic.isEmpty()) {
            Map<String, Object> err = new LinkedHashMap<String, Object>();
            err.put("code", 400);
            err.put("message", "请提供文章主题");
            return ResponseEntity.badRequest().body(err);
        }

        try {
            Map<String, Object> result = articleService.generateAndSaveHybrid(topic, persona);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            Map<String, Object> err = new LinkedHashMap<String, Object>();
            err.put("code", 500);
            err.put("message", "混合架构生成失败：" + e.getMessage());
            return ResponseEntity.internalServerError().body(err);
        }
    }

    /**
     * 统一生成接口（支持模式切换）。
     *
     * 请求体：
     * {"topic": "补钙", "target_crowd": "老年人", "mode": "hybrid"}
     * mode 可选值：rag（方案A，默认）/ hybrid（方案C）
     */
    @PostMapping("/generate-smart")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> generateSmart(@RequestBody Map<String, Object> body) {
        String topic = body != null ? String.valueOf(body.getOrDefault("topic", "")).trim() : "";
        String persona = body != null ? String.valueOf(body.getOrDefault("target_crowd", "普通人群")).trim() : "普通人群";
        String mode = body != null ? String.valueOf(body.getOrDefault("mode", "rag")).trim() : "rag";

        if (topic.isEmpty()) {
            Map<String, Object> err = new LinkedHashMap<String, Object>();
            err.put("code", 400);
            err.put("message", "请提供文章主题");
            return ResponseEntity.badRequest().body(err);
        }

        try {
            Map<String, Object> result;
            if ("hybrid".equalsIgnoreCase(mode)) {
                result = articleService.generateAndSaveHybrid(topic, persona);
            } else {
                result = articleService.generateAndSave(topic, persona);
            }
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            Map<String, Object> err = new LinkedHashMap<String, Object>();
            err.put("code", 500);
            err.put("message", "生成失败：" + e.getMessage());
            return ResponseEntity.internalServerError().body(err);
        }
    }

    // ======================== 异步化接口（阶段一·举措1，同步接口保留兜底） ========================

    /**
     * 异步生成科普文章（RAG 模式）：立即返回 taskId，前端轮询 /task/{taskId} 获取结果。
     * 请求体：{"topic": "补钙", "persona": "老年人"}
     */
    @PostMapping("/generate-async")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> generateArticleAsync(@RequestBody Map<String, String> request) {
        String topic = request != null ? request.get("topic") : null;
        String persona = request != null ? request.get("persona") : null;
        if (persona == null || persona.trim().isEmpty()) {
            persona = "普通人群";
        }
        if (topic == null || topic.trim().isEmpty()) {
            Map<String, Object> err = new LinkedHashMap<String, Object>();
            err.put("code", 400);
            err.put("message", "主题不能为空");
            return ResponseEntity.badRequest().body(err);
        }

        String taskId = asyncArticleTaskService.submitArticleGeneration(topic.trim(), persona);
        Map<String, Object> resp = new LinkedHashMap<String, Object>();
        resp.put("code", 200);
        resp.put("taskId", taskId);
        resp.put("status", "PENDING");
        resp.put("mode", "rag");
        resp.put("message", "生成任务已提交后台执行，请轮询 /api/articles/task/" + taskId + " 获取进度");
        return ResponseEntity.ok(resp);
    }

    /**
     * 异步生成科普文章（混合架构方案C）：立即返回 taskId。
     * 请求体：{"topic": "补钙", "target_crowd": "老年人"}
     */
    @PostMapping("/generate-hybrid-async")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> generateHybridAsync(@RequestBody Map<String, Object> body) {
        String topic = body != null ? String.valueOf(body.getOrDefault("topic", "")).trim() : "";
        String persona = body != null ? String.valueOf(body.getOrDefault("target_crowd", "普通人群")).trim() : "普通人群";

        if (topic.isEmpty()) {
            Map<String, Object> err = new LinkedHashMap<String, Object>();
            err.put("code", 400);
            err.put("message", "请提供文章主题");
            return ResponseEntity.badRequest().body(err);
        }

        String taskId = asyncArticleTaskService.submitHybridGeneration(topic, persona);
        Map<String, Object> resp = new LinkedHashMap<String, Object>();
        resp.put("code", 200);
        resp.put("taskId", taskId);
        resp.put("status", "PENDING");
        resp.put("mode", "hybrid");
        resp.put("message", "混合架构生成任务已提交后台执行，请轮询 /api/articles/task/" + taskId + " 获取进度");
        return ResponseEntity.ok(resp);
    }

    /**
     * 异步自纠错重新生成：立即返回 taskId。
     */
    @PostMapping("/regenerate-async/{articleId}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> regenerateAsync(@PathVariable Integer articleId) {
        String taskId = asyncArticleTaskService.submitRegenerate(articleId);
        Map<String, Object> resp = new LinkedHashMap<String, Object>();
        resp.put("code", 200);
        resp.put("taskId", taskId);
        resp.put("status", "PENDING");
        resp.put("mode", "regenerate");
        resp.put("message", "自纠错重新生成任务已提交后台执行，请轮询 /api/articles/task/" + taskId + " 获取进度");
        return ResponseEntity.ok(resp);
    }

    /**
     * 查询异步任务状态与结果。
     * status：PENDING / RUNNING / SUCCESS / FAILED；成功时 result 携带完整生成结果。
     */
    @GetMapping("/task/{taskId}")
    public ResponseEntity<Map<String, Object>> getTaskStatus(@PathVariable String taskId) {
        return ResponseEntity.ok(asyncArticleTaskService.getTaskStatus(taskId));
    }

    /**
     * SSRF 防护校验：仅允许 http/https 协议，且目标主机不能是
     * 回环地址（127.0.0.1、localhost）、链路本地/站点本地内网地址
     * （10.x、172.16-31.x、192.168.x、169.254.x 等）及保留/组播地址。
     */
    private boolean isSafeFetchUrl(String url) {
        if (url == null || url.trim().isEmpty()) return false;
        String trimmed = url.trim().toLowerCase();
        if (!trimmed.startsWith("http://") && !trimmed.startsWith("https://")) return false;

        try {
            URI uri = URI.create(trimmed);
            String host = uri.getHost();
            if (host == null || host.isEmpty()) return false;
            host = host.toLowerCase();

            // 域名形式：localhost / .local / 数字 IP 文本直接拦截
            if (host.equals("localhost") || host.endsWith(".local")) return false;

            InetAddress address = InetAddress.getByName(host);
            if (address.isLoopbackAddress()) return false;   // 127.0.0.0/8, ::1
            if (address.isAnyLocalAddress()) return false;   // 0.0.0.0
            if (address.isLinkLocalAddress()) return false;  // 169.254.0.0/16, fe80::/10
            if (address.isSiteLocalAddress()) return false;  // 10/8, 172.16/12, 192.168/16, fc00::/7

            // 兜底：显式校验常见内网/保留 IPv4 网段（DNS 重绑定解析到内网时）
            byte[] raw = address.getAddress();
            if (raw != null && raw.length == 4) {
                int b0 = raw[0] & 0xFF;
                int b1 = raw[1] & 0xFF;
                if (b0 == 10) return false;                              // 10.0.0.0/8
                if (b0 == 127) return false;                             // 127.0.0.0/8
                if (b0 == 169 && b1 == 254) return false;                // 169.254.0.0/16
                if (b0 == 172 && b1 >= 16 && b1 <= 31) return false;     // 172.16.0.0/12
                if (b0 == 192 && b1 == 168) return false;                // 192.168.0.0/16
                if (b0 == 100 && b1 >= 64 && b1 <= 127) return false;    // 100.64.0.0/10 CGNAT
                if (b0 >= 224) return false;                             // 组播/保留
            }
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}