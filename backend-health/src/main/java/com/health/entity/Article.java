package com.health.entity;

import javax.persistence.*;
import java.time.LocalDate;

@Entity
@Table(name = "article")
public class Article {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "title", nullable = false)
    private String title;

    @Column(name = "topic")
    private String topic;

    /** 主题分组ID：速读卡/深度文/综述文共享同一个 topicGroupId */
    @Column(name = "topic_group_id")
    private String topicGroupId;

    /** 篇幅类型：short=速读卡, medium=深度文, long=综述文 */
    @Column(name = "length_type")
    private String lengthType = "medium";

    /** 正文内容（markdown）—— 实际按 lengthType 展示 */
    @Column(name = "content", nullable = false, columnDefinition = "TEXT")
    private String content;

    /** 速读卡正文（冗余字段，前端快速取） */
    @Column(name = "content_short", columnDefinition = "TEXT")
    private String contentShort;

    /** 深度文正文 */
    @Column(name = "content_medium", columnDefinition = "TEXT")
    private String contentMedium;

    /** 综述文正文 */
    @Column(name = "content_long", columnDefinition = "TEXT")
    private String contentLong;

    @Column(name = "summary")
    private String summary;

    @Column(name = "summary_short")
    private String summaryShort;

    @Column(name = "summary_medium")
    private String summaryMedium;

    @Column(name = "summary_long")
    private String summaryLong;

    @Column(name = "tags", columnDefinition = "TEXT")
    private String tags;

    @Column(name = "category")
    private String category;

    @Column(name = "audience")
    private String audience;

    @Column(name = "word_count")
    private Integer wordCount;

    /** 参考文献 JSON 数组字符串：["[1] xx", "[2] yy"] */
    @Column(name = "sources_json", columnDefinition = "TEXT")
    private String sourcesJson;

    @Column(name = "views_count")
    private Integer viewsCount = 0;

    @Column(name = "likes_count")
    private Integer likesCount = 0;

    @Column(name = "created_at")
    private LocalDate createdAt = LocalDate.now();

    @Column(name = "updated_at")
    private LocalDate updatedAt = LocalDate.now();

    /** pending_review / approved / published / rejected / archived */
    @Column(name = "status")
    private String status = "published";

    @Column(name = "source")
    private String source = "ai";

    @Column(name = "quality_score")
    private Integer qualityScore;

    @Column(name = "has_errors_reported")
    private Boolean hasErrorsReported = false;

    public Article() {}

    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getTopic() { return topic; }
    public void setTopic(String topic) { this.topic = topic; }
    public String getTopicGroupId() { return topicGroupId; }
    public void setTopicGroupId(String topicGroupId) { this.topicGroupId = topicGroupId; }
    public String getLengthType() { return lengthType; }
    public void setLengthType(String lengthType) { this.lengthType = lengthType; }
    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }
    public String getContentShort() { return contentShort; }
    public void setContentShort(String contentShort) { this.contentShort = contentShort; }
    public String getContentMedium() { return contentMedium; }
    public void setContentMedium(String contentMedium) { this.contentMedium = contentMedium; }
    public String getContentLong() { return contentLong; }
    public void setContentLong(String contentLong) { this.contentLong = contentLong; }
    public String getSummary() { return summary; }
    public void setSummary(String summary) { this.summary = summary; }
    public String getSummaryShort() { return summaryShort; }
    public void setSummaryShort(String summaryShort) { this.summaryShort = summaryShort; }
    public String getSummaryMedium() { return summaryMedium; }
    public void setSummaryMedium(String summaryMedium) { this.summaryMedium = summaryMedium; }
    public String getSummaryLong() { return summaryLong; }
    public void setSummaryLong(String summaryLong) { this.summaryLong = summaryLong; }
    public String getTags() { return tags; }
    public void setTags(String tags) { this.tags = tags; }
    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }
    public String getAudience() { return audience; }
    public void setAudience(String audience) { this.audience = audience; }
    public Integer getWordCount() { return wordCount; }
    public void setWordCount(Integer wordCount) { this.wordCount = wordCount; }
    public String getSourcesJson() { return sourcesJson; }
    public void setSourcesJson(String sourcesJson) { this.sourcesJson = sourcesJson; }
    public Integer getViewsCount() { return viewsCount; }
    public void setViewsCount(Integer viewsCount) { this.viewsCount = viewsCount; }
    public Integer getLikesCount() { return likesCount; }
    public void setLikesCount(Integer likesCount) { this.likesCount = likesCount; }
    public LocalDate getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDate createdAt) { this.createdAt = createdAt; }
    public LocalDate getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDate updatedAt) { this.updatedAt = updatedAt; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }
    public Integer getQualityScore() { return qualityScore; }
    public void setQualityScore(Integer qualityScore) { this.qualityScore = qualityScore; }
    public Boolean getHasErrorsReported() { return hasErrorsReported; }
    public void setHasErrorsReported(Boolean hasErrorsReported) { this.hasErrorsReported = hasErrorsReported; }
}