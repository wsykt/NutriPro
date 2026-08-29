package com.health.controller;

import com.health.dto.ApiResponse;
import com.health.entity.AiPreviewSnapshot;
import com.health.service.AiPreviewService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 匿名（无需 JWT）的快照打开接口，配合前端路由 "/admin/preview/open/:id?tok=..." 做 iframe 预览 / 新标签页预览。
 * 安全：必须携带 5 分钟内有效的 preview_token（一次性；用完立刻失效）。
 * 只提供 GET，不允许匿名写。
 */
@RestController
@RequestMapping("/api/preview")
public class AiPreviewOpenController {

    private final AiPreviewService aiPreviewService;
    private final ObjectMapper om = new ObjectMapper();

    public AiPreviewOpenController(AiPreviewService aiPreviewService) {
        this.aiPreviewService = aiPreviewService;
    }

    @GetMapping("/open/{id}")
    public ResponseEntity<ApiResponse<Map<String, Object>>> open(@PathVariable Integer id,
                                                                 @RequestParam("tok") String tok) {
        if (tok == null || tok.trim().isEmpty()) {
            return ResponseEntity.status(401).body(ApiResponse.<Map<String, Object>>error("缺少匿名预览 tok 参数"));
        }
        AiPreviewSnapshot snap = aiPreviewService.findByPreviewTokenAndTokenExpireAtAfter(tok, LocalDateTime.now()).orElse(null);
        if (snap == null || !snap.getId().equals(id)) {
            return ResponseEntity.status(401).body(ApiResponse.<Map<String, Object>>error("预览令牌无效或已过期，请重新生成"));
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", snap.getId());
        m.put("sessionId", snap.getSessionId());
        m.put("userId", snap.getUserId());
        m.put("funcType", snap.getFuncType());
        m.put("mode", snap.getMode());
        m.put("title", snap.getTitle());
        m.put("summary", snap.getSummary());
        m.put("published", Integer.valueOf(1).equals(snap.getPublished()));
        m.put("publishedAt", snap.getPublishedAt() != null ? snap.getPublishedAt().toString() : null);
        m.put("targetId", snap.getTargetId());
        try { m.put("payload", om.readValue(snap.getPayloadJson(), Object.class)); }
        catch (Exception e) { m.put("payload", snap.getPayloadJson()); }

        // 一次性：消费后立刻清掉 token
        snap.setPreviewToken(null);
        snap.setTokenExpireAt(null);
        aiPreviewService.save(snap);
        return ResponseEntity.ok(ApiResponse.success(m));
    }

    /** 调试用健康检查（匿名） */
    @GetMapping("/ping")
    public ResponseEntity<ApiResponse<Map<String, Object>>> ping() {
        Map<String, Object> m = new HashMap<>();
        m.put("service", "AiPreviewOpen");
        m.put("now", LocalDateTime.now().toString());
        return ResponseEntity.ok(ApiResponse.success(m));
    }
}
