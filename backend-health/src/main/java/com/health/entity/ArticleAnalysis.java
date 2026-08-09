package com.health.entity;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "article_analysis")
public class ArticleAnalysis {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "article_id", nullable = false)
    private Integer articleId;

    @Column(name = "quality_score")
    private Integer qualityScore;

    /** 问题列表 JSON：[{"type":"结构问题","severity":"high","description":"...","suggestion":"..."}] */
    @Column(name = "issues_json", columnDefinition = "TEXT")
    private String issuesJson;

    /** 优化建议 */
    @Column(name = "suggestions", columnDefinition = "TEXT")
    private String suggestions;

    /** AI生成的优化后内容（可选） */
    @Column(name = "optimized_content", columnDefinition = "TEXT")
    private String optimizedContent;

    /** 分析状态：pending / completed / applied */
    @Column(name = "status")
    private String status = "pending";

    /** 提示词版本号，用于持续优化 */
    @Column(name = "prompt_version")
    private String promptVersion;

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();

    @Column(name = "updated_at")
    private LocalDateTime updatedAt = LocalDateTime.now();

    public ArticleAnalysis() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Integer getArticleId() { return articleId; }
    public void setArticleId(Integer articleId) { this.articleId = articleId; }
    public Integer getQualityScore() { return qualityScore; }
    public void setQualityScore(Integer qualityScore) { this.qualityScore = qualityScore; }
    public String getIssuesJson() { return issuesJson; }
    public void setIssuesJson(String issuesJson) { this.issuesJson = issuesJson; }
    public String getSuggestions() { return suggestions; }
    public void setSuggestions(String suggestions) { this.suggestions = suggestions; }
    public String getOptimizedContent() { return optimizedContent; }
    public void setOptimizedContent(String optimizedContent) { this.optimizedContent = optimizedContent; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getPromptVersion() { return promptVersion; }
    public void setPromptVersion(String promptVersion) { this.promptVersion = promptVersion; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
