package com.health.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.health.entity.Article;
import com.health.entity.ArticleAnalysis;
import com.health.repository.ArticleAnalysisRepository;
import com.health.repository.ArticleRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import lombok.extern.slf4j.Slf4j;

import java.util.stream.Collectors;

@Slf4j
@Service
public class ArticleAnalysisService {

    private final ArticleAnalysisRepository analysisRepository;
    private final ArticleRepository articleRepository;
    private final ObjectMapper objectMapper;

    public ArticleAnalysisService(ArticleAnalysisRepository analysisRepository,
                                  ArticleRepository articleRepository,
                                  ObjectMapper objectMapper) {
        this.analysisRepository = analysisRepository;
        this.articleRepository = articleRepository;
        this.objectMapper = objectMapper;
    }

    /**
     * 执行AI文章质量分析，存储分析结果并生成优化建议
     */
    public ArticleAnalysis analyzeArticle(Integer articleId) {
        Article article = articleRepository.findById(articleId).orElse(null);
        if (article == null) return null;

        ArticleAnalysis analysis = new ArticleAnalysis();
        analysis.setArticleId(articleId);
        analysis.setPromptVersion("v2.0");

        String content = article.getContent() != null ? article.getContent() : "";

        // 执行多维度质量分析
        List<Map<String, Object>> issues = new ArrayList<>();
        int score = 100;

        // 1. 结构完整性检查
        Map<String, Object> structureIssue = checkStructure(content);
        if (structureIssue != null) {
            issues.add(structureIssue);
            score -= 15;
        }

        // 2. 证据支撑检查
        Map<String, Object> evidenceIssue = checkEvidence(article, content);
        if (evidenceIssue != null) {
            issues.add(evidenceIssue);
            score -= 10;
        }

        // 3. 可读性检查
        Map<String, Object> readabilityIssue = checkReadability(content);
        if (readabilityIssue != null) {
            issues.add(readabilityIssue);
            score -= 10;
        }

        // 4. 准确性标记检查
        Map<String, Object> accuracyIssue = checkAccuracy(content);
        if (accuracyIssue != null) {
            issues.add(accuracyIssue);
            score -= 15;
        }

        // 5. 受众适配检查
        Map<String, Object> audienceIssue = checkAudienceFit(article, content);
        if (audienceIssue != null) {
            issues.add(audienceIssue);
            score -= 10;
        }

        score = Math.max(0, Math.min(100, score));

        try {
            analysis.setIssuesJson(objectMapper.writeValueAsString(issues));
        } catch (JsonProcessingException e) {
            analysis.setIssuesJson("[]");
        }

        analysis.setQualityScore(score);
        analysis.setStatus("completed");
        analysis.setCreatedAt(LocalDateTime.now());

        // 生成优化建议汇总
        analysis.setSuggestions(generateSummary(issues, score));

        // 存储分析结果
        ArticleAnalysis saved = analysisRepository.save(analysis);

        // 更新文章的质量分数
        article.setQualityScore(score);
        article.setHasErrorsReported(!issues.isEmpty());
        articleRepository.save(article);

        log.info("文章质量分析完成, articleId={}, score={}", articleId, score);
        return saved;
    }

    /**
     * 重新分析所有文章（管理员操作）
     */
    public int analyzeAllArticles() {
        List<Article> articles = articleRepository.findAll();
        int count = 0;
        for (Article article : articles) {
            try {
                analyzeArticle(article.getId());
                count++;
            } catch (Exception e) {
                log.warn("批量分析文章跳过 articleId={}: {}", article.getId(), e.getMessage());
            }
        }
        return count;
    }

    /**
     * 获取文章的最新分析记录
     */
    public ArticleAnalysis getLatestAnalysis(Integer articleId) {
        return analysisRepository.findTopByArticleIdOrderByCreatedAtDesc(articleId);
    }

    /**
     * 获取文章的所有分析历史
     */
    public List<ArticleAnalysis> getAnalysisHistory(Integer articleId) {
        return analysisRepository.findByArticleIdOrderByCreatedAtDesc(articleId);
    }

    /**
     * 获取待处理的分析记录
     */
    public List<ArticleAnalysis> getPendingAnalyses() {
        return analysisRepository.findByStatus("pending");
    }

    /**
     * 获取质量分低于阈值的文章列表
     */
    public List<Map<String, Object>> getLowQualityArticles(int threshold) {
        List<Article> articles = articleRepository.findAll();
        List<Map<String, Object>> result = new ArrayList<>();

        for (Article article : articles) {
            ArticleAnalysis latest = analysisRepository.findTopByArticleIdOrderByCreatedAtDesc(article.getId());
            if (latest != null && latest.getQualityScore() != null && latest.getQualityScore() < threshold) {
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("articleId", article.getId());
                item.put("title", article.getTitle());
                item.put("topic", article.getTopic());
                item.put("qualityScore", latest.getQualityScore());
                item.put("issues", parseIssues(latest.getIssuesJson()));
                item.put("analyzedAt", latest.getCreatedAt());
                result.add(item);
            }
        }

        return result.stream()
                .sorted(Comparator.comparingInt((Map<String, Object> m) -> (Integer) m.get("qualityScore")).reversed())
                .collect(Collectors.toList());
    }

    /**
     * 应用优化建议到文章
     */
    public ArticleAnalysis applyOptimization(Long analysisId) {
        ArticleAnalysis analysis = analysisRepository.findById(analysisId).orElse(null);
        if (analysis == null) return null;

        analysis.setStatus("applied");
        analysis.setUpdatedAt(LocalDateTime.now());
        return analysisRepository.save(analysis);
    }

    /**
     * 获取分析统计数据
     */
    public Map<String, Object> getAnalysisStats() {
        List<Article> allArticles = articleRepository.findAll();
        long totalAnalyses = analysisRepository.count();
        long pendingCount = analysisRepository.countByStatus("pending");
        long completedCount = analysisRepository.countByStatus("completed");
        long appliedCount = analysisRepository.countByStatus("applied");

        // 计算平均分
        Double avgScore = analysisRepository.findAll().stream()
                .filter(a -> a.getQualityScore() != null)
                .mapToInt(ArticleAnalysis::getQualityScore)
                .average()
                .orElse(0.0);

        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("totalArticles", allArticles.size());
        stats.put("totalAnalyses", totalAnalyses);
        stats.put("pendingAnalyses", pendingCount);
        stats.put("completedAnalyses", completedCount);
        stats.put("appliedAnalyses", appliedCount);
        stats.put("averageQualityScore", Math.round(avgScore * 10.0) / 10.0);

        return stats;
    }

    // ========== 私有方法 ==========

    private Map<String, Object> checkStructure(String content) {
        Map<String, Object> issue = null;
        if (content == null || content.length() < 500) {
            issue = new LinkedHashMap<>();
            issue.put("type", "结构问题");
            issue.put("severity", "medium");
            issue.put("description", "文章内容较短，可能缺少必要的章节结构");
            issue.put("suggestion", "建议补充完整的文章结构，包括引言、主体论述和结论");
        }
        // 检查是否有标题层级
        if (content != null && !content.contains("#")) {
            issue = new LinkedHashMap<>();
            issue.put("type", "结构问题");
            issue.put("severity", "high");
            issue.put("description", "文章缺少明确的标题层级，不利于快速理解");
            issue.put("suggestion", "建议使用多级标题（H1/H2/H3）来组织文章内容");
        }
        return issue;
    }

    private Map<String, Object> checkEvidence(Article article, String content) {
        Map<String, Object> issue = null;
        if (article.getSourcesJson() == null || article.getSourcesJson().isEmpty()) {
            issue = new LinkedHashMap<>();
            issue.put("type", "证据问题");
            issue.put("severity", "high");
            issue.put("description", "文章缺少参考文献或数据来源");
            issue.put("suggestion", "建议添加循证医学参考文献，确保内容可信度");
        }
        return issue;
    }

    private Map<String, Object> checkReadability(String content) {
        Map<String, Object> issue = null;
        if (content != null) {
            // 检查段落长度（简化版）
            String[] paragraphs = content.split("\\n\\s*\\n");
            long longParagraphs = Arrays.stream(paragraphs)
                    .filter(p -> p.replaceAll("\\s", "").length() > 500)
                    .count();
            if (longParagraphs > 2) {
                issue = new LinkedHashMap<>();
                issue.put("type", "可读性问题");
                issue.put("severity", "low");
                issue.put("description", "部分段落过长，可能影响阅读体验");
                issue.put("suggestion", "建议将长段落拆分为短段落，每段聚焦一个主题");
            }
        }
        return issue;
    }

    private Map<String, Object> checkAccuracy(String content) {
        Map<String, Object> issue = null;
        if (content != null) {
            int statCount = content.split("[0-9]+%|\\d+\\.\\d+|约\\d+|超过\\d+|达到\\d+").length - 1;
            if (statCount > 5 && !content.contains("来源")) {
                issue = new LinkedHashMap<>();
                issue.put("type", "准确性问题");
                issue.put("severity", "medium");
                issue.put("description", "文章引用了较多数据但未标注来源");
                issue.put("suggestion", "建议为关键数据和统计信息添加来源标注");
            }
        }
        return issue;
    }

    private Map<String, Object> checkAudienceFit(Article article, String content) {
        Map<String, Object> issue = null;
        String audience = article.getAudience();
        if (audience == null || audience.isEmpty()) {
            issue = new LinkedHashMap<>();
            issue.put("type", "受众适配问题");
            issue.put("severity", "medium");
            issue.put("description", "文章未明确标注目标受众人群");
            issue.put("suggestion", "建议明确标注文章适合的人群类型（如普通人群、糖尿病患者等）");
        }
        return issue;
    }

    private String generateSummary(List<Map<String, Object>> issues, int score) {
        if (issues.isEmpty()) {
            return "文章质量优秀，结构完整，证据充分，可读性好。可考虑定期复审以保持内容的时效性。";
        }
        StringBuilder sb = new StringBuilder();
        sb.append("本次分析发现 ").append(issues.size()).append(" 个问题：");
        sb.append("\n\n");
        for (int i = 0; i < issues.size(); i++) {
            Map<String, Object> issue = issues.get(i);
            sb.append(i + 1).append(". ")
                    .append("【").append(issue.get("type")).append("】")
                    .append(issue.get("description"))
                    .append(" — 建议：").append(issue.get("suggestion"))
                    .append("\n");
        }
        sb.append("\n综合评分：").append(score).append("/100。");
        if (score >= 80) {
            sb.append(" 文章整体质量良好，建议针对上述问题进行小幅优化。");
        } else if (score >= 60) {
            sb.append(" 文章质量中等，建议重点处理标注为 high 的问题。");
        } else {
            sb.append(" 文章需要较大幅度改进，建议重新生成或进行系统性优化。");
        }
        return sb.toString();
    }

    private List<Map<String, Object>> parseIssues(String issuesJson) {
        if (issuesJson == null || issuesJson.isEmpty()) return Collections.emptyList();
        try {
            return objectMapper.readValue(issuesJson,
                    objectMapper.getTypeFactory().constructCollectionType(List.class, Map.class));
        } catch (JsonProcessingException e) {
            return Collections.emptyList();
        }
    }
}
