package com.health.entity;

import javax.persistence.*;
import java.time.LocalDateTime;

/**
 * AI 功能的管理员"先预览→再发布"快照。
 * 用于流程展示页：跑完 AI 后先不落业务表，管理员看效果满意再点"喜欢+发布"。
 * 仅文章类型会在发布时真正写入 articles 主表（走 ArticleService.createArticle）；
 * 其他类型（食谱/训练/对话/周报/膳食计划）暂只打 published=1 标记，不写主业务表（演示优先）。
 */
@Entity
@Table(name = "ai_preview_snapshot")
public class AiPreviewSnapshot {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "session_id", nullable = false, length = 64)
    private String sessionId;

    @Column(name = "user_id")
    private Integer userId;

    /** article / recipe / training / consult / weeklyReport / dietPlan / nutrition */
    @Column(name = "func_type", nullable = false, length = 32)
    private String funcType;

    /** normal / high_performance / offline */
    @Column(name = "mode", nullable = false, length = 16)
    private String mode = "normal";

    @Column(name = "title", length = 512)
    private String title;

    @Column(name = "summary", columnDefinition = "TEXT")
    private String summary;

    /** 对应前端权威组件所需的完整 JSON（字段名严格匹配）。 */
    @Column(name = "payload_json", nullable = false, columnDefinition = "TEXT")
    private String payloadJson;

    /** 匿名一次性预览用 token（iframe/新开标签页可绕过 JWT），5 分钟内仅 1 次有效。 */
    @Column(name = "preview_token", length = 64)
    private String previewToken;

    @Column(name = "token_expire_at")
    private LocalDateTime tokenExpireAt;

    @Column(name = "published")
    private Integer published = 0;

    @Column(name = "published_at")
    private LocalDateTime publishedAt;

    /** 发布后若主业务生成了 ID（如 article.id）回写到这。 */
    @Column(name = "target_id")
    private Integer targetId;

    @Column(name = "note", length = 512)
    private String note;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        LocalDateTime now = LocalDateTime.now();
        if (this.createdAt == null) this.createdAt = now;
        if (this.updatedAt == null) this.updatedAt = now;
    }

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }

    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }
    public String getSessionId() { return sessionId; }
    public void setSessionId(String sessionId) { this.sessionId = sessionId; }
    public Integer getUserId() { return userId; }
    public void setUserId(Integer userId) { this.userId = userId; }
    public String getFuncType() { return funcType; }
    public void setFuncType(String funcType) { this.funcType = funcType; }
    public String getMode() { return mode; }
    public void setMode(String mode) { this.mode = mode; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getSummary() { return summary; }
    public void setSummary(String summary) { this.summary = summary; }
    public String getPayloadJson() { return payloadJson; }
    public void setPayloadJson(String payloadJson) { this.payloadJson = payloadJson; }
    public String getPreviewToken() { return previewToken; }
    public void setPreviewToken(String previewToken) { this.previewToken = previewToken; }
    public LocalDateTime getTokenExpireAt() { return tokenExpireAt; }
    public void setTokenExpireAt(LocalDateTime tokenExpireAt) { this.tokenExpireAt = tokenExpireAt; }
    public Integer getPublished() { return published; }
    public void setPublished(Integer published) { this.published = published; }
    public LocalDateTime getPublishedAt() { return publishedAt; }
    public void setPublishedAt(LocalDateTime publishedAt) { this.publishedAt = publishedAt; }
    public Integer getTargetId() { return targetId; }
    public void setTargetId(Integer targetId) { this.targetId = targetId; }
    public String getNote() { return note; }
    public void setNote(String note) { this.note = note; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
