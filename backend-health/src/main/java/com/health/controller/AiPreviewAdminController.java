package com.health.controller;

import com.health.dto.ApiResponse;
import com.health.entity.AiPreviewSnapshot;
import com.health.entity.Article;
import com.health.repository.AiPreviewSnapshotRepository;
import com.health.service.ArticleService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 管理员 AI 功能 · 先预览后发布 流程：
 * <pre>
 *   1. POST /api/admin/preview/snapshot      存一次 AI 产出快照（管理员专用）
 *   2. GET  /api/admin/preview/snapshot/{id} 取快照（需 JWT，流程面板调用）
 *   3. POST /api/admin/preview/snapshot/{id}/generateToken 生成匿名预览 token（iframe/new-tab 可访问）
 *   4. GET  /api/admin/preview/list?sessionId=   该 session 下所有快照列表（新→旧）
 *   5. POST /api/admin/preview/snapshot/{id}/publish  点"喜欢+发布"：
 *        - article 类型：真正调用 ArticleService.createArticle() 落 articles 表，status=published
 *        - 其他类型：仅快照 published=1 打标，暂不写主业务表（演示用）
 *   6. 匿名 GET  /api/preview/open/{id}?tok=...（见 AiPreviewOpenController）
 * </pre>
 */
@RestController
@RequestMapping("/api/admin/preview")
@PreAuthorize("hasRole('ADMIN')")
public class AiPreviewAdminController {

    private final AiPreviewSnapshotRepository repo;
    private final ArticleService articleService;
    private final ObjectMapper om = new ObjectMapper();

    public AiPreviewAdminController(AiPreviewSnapshotRepository repo, ArticleService articleService) {
        this.repo = repo;
        this.articleService = articleService;
    }

    /** 1. 保存 AI 产出快照 */
    @PostMapping("/snapshot")
    public ResponseEntity<ApiResponse<Map<String, Object>>> saveSnapshot(@RequestBody Map<String, Object> payload) {
        String sessionId = (String) payload.get("sessionId");
        String funcType = (String) payload.get("funcType");
        if (sessionId == null || sessionId.trim().isEmpty()) sessionId = "s-" + UUID.randomUUID().toString().replace("-", "").substring(0, 12);
        if (funcType == null || funcType.trim().isEmpty()) {
            return ResponseEntity.badRequest().body(ApiResponse.<Map<String, Object>>error("funcType 必填 (article|recipe|training|consult|weeklyReport|dietPlan|nutrition)"));
        }
        Object payloadObj = payload.get("payload");
        if (payloadObj == null) {
            return ResponseEntity.badRequest().body(ApiResponse.<Map<String, Object>>error("payload 必填（完整前端权威组件 JSON）"));
        }
        AiPreviewSnapshot snap = new AiPreviewSnapshot();
        snap.setSessionId(sessionId);
        Number userIdNum = payload.get("userId") instanceof Number ? (Number) payload.get("userId") : null;
        if (userIdNum != null) snap.setUserId(userIdNum.intValue());
        snap.setFuncType(funcType);
        String mode = (String) payload.get("mode");
        snap.setMode(mode == null || mode.trim().isEmpty() ? "normal" : mode);
        snap.setTitle((String) payload.get("title"));
        snap.setSummary((String) payload.get("summary"));
        snap.setNote((String) payload.get("note"));
        try {
            snap.setPayloadJson(om.writeValueAsString(payloadObj));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(ApiResponse.error("payload JSON 序列化失败：" + e.getMessage()));
        }
        snap = repo.save(snap);
        Map<String, Object> out = toMap(snap, true);
        return ResponseEntity.ok(ApiResponse.success(out));
    }

    /** 2. 管理员取快照详情 */
    @GetMapping("/snapshot/{id}")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getSnapshot(@PathVariable Integer id) {
        Optional<AiPreviewSnapshot> opt = repo.findById(id);
        if (!opt.isPresent()) return ResponseEntity.status(404).body(ApiResponse.<Map<String, Object>>error("snapshot not found: id=" + id));
        return ResponseEntity.ok(ApiResponse.success(toMap(opt.get(), true)));
    }

    /** 3. 生成匿名一次性 token（5 分钟内有效），配合 open/{id}?tok=... 做 iframe / 新标签页预览 */
    @PostMapping("/snapshot/{id}/generateToken")
    public ResponseEntity<ApiResponse<Map<String, Object>>> generateToken(@PathVariable Integer id) {
        Optional<AiPreviewSnapshot> opt = repo.findById(id);
        if (!opt.isPresent()) return ResponseEntity.status(404).body(ApiResponse.<Map<String, Object>>error("snapshot not found"));
        AiPreviewSnapshot snap = opt.get();
        String tok = "pt-" + UUID.randomUUID().toString().replace("-", "");
        snap.setPreviewToken(tok);
        snap.setTokenExpireAt(LocalDateTime.now().plusMinutes(5));
        repo.save(snap);
        Map<String, Object> out = new HashMap<>();
        out.put("id", snap.getId());
        out.put("previewToken", tok);
        out.put("expireAt", snap.getTokenExpireAt().toString());
        out.put("url", "/admin/preview/open/" + snap.getId() + "?tok=" + tok);
        return ResponseEntity.ok(ApiResponse.success(out));
    }

    /** 4. 某个 session 下的所有快照 */
    @GetMapping("/list")
    public ResponseEntity<ApiResponse<List<Map<String, Object>>>> listBySession(@RequestParam String sessionId) {
        List<AiPreviewSnapshot> list = repo.findBySessionIdOrderByIdDesc(sessionId);
        List<Map<String, Object>> out = list.stream().map(s -> toMap(s, false)).collect(Collectors.toList());
        return ResponseEntity.ok(ApiResponse.success(out));
    }

    /**
     * 5. 发布（管理员点"喜欢+发布"）
     *  - article → 真正落 articles 主表，复用文章管理的 ArticleService.createArticle，status=published
     *  - 其他类型 → 只打 published=1 标记 + 写 publishedAt，暂不写主业务表（演示优先）
     */
    @PostMapping("/snapshot/{id}/publish")
    public ResponseEntity<ApiResponse<Map<String, Object>>> publish(@PathVariable Integer id) {
        Optional<AiPreviewSnapshot> opt = repo.findById(id);
        if (!opt.isPresent()) return ResponseEntity.status(404).body(ApiResponse.<Map<String, Object>>error("snapshot not found"));
        AiPreviewSnapshot snap = opt.get();
        if (Integer.valueOf(1).equals(snap.getPublished())) {
            Map<String, Object> out = new HashMap<>();
            out.put("id", snap.getId());
            out.put("published", true);
            out.put("targetId", snap.getTargetId());
            out.put("note", "已发布（重复发布被忽略）");
            return ResponseEntity.ok(ApiResponse.success(out));
        }
        LocalDateTime now = LocalDateTime.now();
        snap.setPublished(1);
        snap.setPublishedAt(now);
        Map<String, Object> resp = new HashMap<>();
        resp.put("id", snap.getId());
        resp.put("funcType", snap.getFuncType());
        resp.put("published", true);

        Object payload;
        try {
            payload = om.readValue(snap.getPayloadJson(), Object.class);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(ApiResponse.<Map<String, Object>>error("payload JSON 反序列化失败：" + e.getMessage()));
        }

        if ("article".equalsIgnoreCase(snap.getFuncType()) && payload instanceof Map) {
            Map<?, ?> pm = (Map<?, ?>) payload;
            Article art = new Article();
            art.setTitle(str(pm, "title", snap.getTitle(), "未命名科普文章"));
            art.setTopic(str(pm, "topic", null));
            art.setTopicGroupId(str(pm, "topicGroupId", null));
            art.setLengthType(str(pm, "lengthType", "medium"));
            art.setContent(str(pm, "content", str(pm, "contentMedium", "# 正文\n\n（AI 生成）")));
            art.setContentShort(str(pm, "contentShort", null));
            art.setContentMedium(str(pm, "contentMedium", null));
            art.setContentLong(str(pm, "contentLong", null));
            art.setSummary(str(pm, "summary", null));
            art.setSummaryShort(str(pm, "summaryShort", null));
            art.setSummaryMedium(str(pm, "summaryMedium", null));
            art.setSummaryLong(str(pm, "summaryLong", null));
            art.setTags(str(pm, "tags", null));
            art.setCategory(str(pm, "category", "AI生成"));
            art.setAudience(str(pm, "audience", null));
            Object wc = pm.get("wordCount");
            if (wc instanceof Number) art.setWordCount(((Number) wc).intValue());
            Object sources = pm.get("sourcesJson");
            if (sources instanceof String) art.setSourcesJson((String) sources);
            else if (sources != null) {
                try { art.setSourcesJson(om.writeValueAsString(sources)); } catch (Exception ignored) {}
            }
            Object qs = pm.get("qualityScore");
            if (qs instanceof Number) art.setQualityScore(((Number) qs).intValue());
            Article saved = articleService.createArticle(art);
            snap.setTargetId(saved.getId());
            resp.put("targetId", saved.getId());
            resp.put("targetType", "article");
            resp.put("note", "文章已发布到【文章管理】（status=published，可直接在前端首页查看）");
        } else {
            resp.put("note", "【演示用】快照已打 published=1 标记；暂未写入主业务表（主业务写入留待下一阶段）");
            resp.put("targetType", "snapshot-only");
        }
        repo.save(snap);
        resp.put("publishedAt", snap.getPublishedAt().toString());
        return ResponseEntity.ok(ApiResponse.success(resp));
    }

    private static String str(Map<?, ?> m, String key, String fallback) {
        return str(m, key, null, fallback);
    }
    private static String str(Map<?, ?> m, String key, String fallback1, String fallback) {
        Object v = m.get(key);
        if (v != null && !v.toString().trim().isEmpty()) return v.toString();
        if (fallback1 != null && !fallback1.trim().isEmpty()) return fallback1;
        return fallback;
    }

    private Map<String, Object> toMap(AiPreviewSnapshot s, boolean withPayload) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", s.getId());
        m.put("sessionId", s.getSessionId());
        m.put("userId", s.getUserId());
        m.put("funcType", s.getFuncType());
        m.put("mode", s.getMode());
        m.put("title", s.getTitle());
        m.put("summary", s.getSummary());
        m.put("published", Integer.valueOf(1).equals(s.getPublished()));
        m.put("publishedAt", s.getPublishedAt() != null ? s.getPublishedAt().toString() : null);
        m.put("targetId", s.getTargetId());
        m.put("note", s.getNote());
        m.put("createdAt", s.getCreatedAt() != null ? s.getCreatedAt().toString() : null);
        m.put("updatedAt", s.getUpdatedAt() != null ? s.getUpdatedAt().toString() : null);
        if (withPayload) {
            try { m.put("payload", om.readValue(s.getPayloadJson(), Object.class)); }
            catch (Exception e) { m.put("payload", s.getPayloadJson()); }
        }
        return m;
    }
}
