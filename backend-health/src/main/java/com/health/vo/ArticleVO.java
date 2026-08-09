package com.health.vo;

import com.health.entity.Article;

import java.time.LocalDate;

public class ArticleVO {

    private Integer id;
    private String title;
    private String topic;
    private String topicGroupId;
    private String lengthType;
    private String content;
    private String summary;
    private String summaryShort;
    private String summaryMedium;
    private String summaryLong;
    private String tags;
    private String category;
    private String audience;
    private Integer wordCount;
    private String sourcesJson;
    private LocalDate createdAt;
    private LocalDate updatedAt;
    private String status;
    private String source;
    private Integer qualityScore;

    public ArticleVO() {}

    public static ArticleVO fromEntity(Article article) {
        if (article == null) return null;
        ArticleVO vo = new ArticleVO();
        vo.setId(article.getId());
        vo.setTitle(article.getTitle());
        vo.setTopic(article.getTopic());
        vo.setTopicGroupId(article.getTopicGroupId());
        vo.setLengthType(article.getLengthType());
        vo.setContent(article.getContent());
        vo.setSummary(article.getSummary());
        vo.setSummaryShort(article.getSummaryShort());
        vo.setSummaryMedium(article.getSummaryMedium());
        vo.setSummaryLong(article.getSummaryLong());
        vo.setTags(article.getTags());
        vo.setCategory(article.getCategory());
        vo.setAudience(article.getAudience());
        vo.setWordCount(article.getWordCount());
        vo.setSourcesJson(article.getSourcesJson());
        vo.setCreatedAt(article.getCreatedAt());
        vo.setUpdatedAt(article.getUpdatedAt());
        vo.setStatus(article.getStatus());
        vo.setSource(article.getSource());
        vo.setQualityScore(article.getQualityScore());
        return vo;
    }

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
}
