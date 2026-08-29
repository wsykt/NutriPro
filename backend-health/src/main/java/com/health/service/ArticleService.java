package com.health.service;

import com.health.config.RestClientConfig;
import com.health.entity.Article;
import com.health.entity.ArticleAnalysis;
import com.health.repository.ArticleAnalysisRepository;
import com.health.repository.ArticleRepository;
import com.health.util.ArticleSplitUtil;
import com.health.util.RagVectorSearchUtil;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import lombok.extern.slf4j.Slf4j;

import javax.annotation.PostConstruct;
import java.util.stream.Collectors;

@Slf4j
@Service
public class ArticleService {

    /** 基础约束模板：所有 Prompt 共用的人设 + 硬性约束（v3.1 强化版 - 带来源渠道标注） */
    private static final String BASE_PROMPT_TEMPLATE =
            "你是一位严谨的营养学科普编辑。所有输出必须遵守以下规则：\n" +
            "1. 严格区分确定循证结论与学术争议内容，争议内容固定放置争议专区；\n" +
            "2. 实操建议整理为清单形式，适配前端卡片展示；\n" +
            "3. 语言为严谨大众科普文风，兼顾专业性与可读性；\n" +
            "4. 【#标记名#】必须独占完整一行，该行不能附带空格、文字、符号；不允许修改标记文本。格式出现偏差时优先保证全部标记完整输出；\n" +
            "5. 营养数据、膳食准则优先使用下方提供的知识库资料，禁止编造数值；\n" +
            "6. 涉及疾病膳食建议，需要标注：建议咨询医生或营养师；\n" +
            "7. 严格控制各个章节字数区间，保障后续拆分速读卡、深度文、综述文效果；\n" +
            "8. 参考文献优先使用本次RAG检索命中的原始权威资料；严禁凭空编造论文、期刊、研究数据。若检索素材缺少完整文献信息，不可虚构参考文献条目，可标注「参考：中国居民膳食指南2022」；\n" +
            "9. 禁止使用绝对化表述（一定、根治、百分百、特效）；膳食建议采用「建议、有助于、优先选择」等严谨措辞；\n" +
            "10. 多条参考素材观点存在分歧时，统一放入学术争议板块完整陈列；不可主观取舍、掩盖不同学术观点；\n" +
            "11. 所有引用素材必须标注来源类型：[向量知识库]（本地BGE检索命中）或 [Agent联网搜索]（Agent通过PubMed等渠道搜集）；\n" +
            "12. 引用素材时需区分来源渠道（v3.1新增）：PubMed科研文献/官方指南/权威报告，便于溯源核查。";

    /** 篇幅后缀映射 */
    private static final Map<String, String> LEN_SUFFIX = new LinkedHashMap<String, String>();
    static {
        LEN_SUFFIX.put("short", "【速读卡】");
        LEN_SUFFIX.put("medium", "【深度文】");
        LEN_SUFFIX.put("long", "【综述文】");
    }

    @Autowired
    private ArticleRepository articleRepository;

    @Autowired
    private AiChatClientService aiChatClientService;

    @Autowired
    private ArticleAnalysisRepository articleAnalysisRepository;

    @Autowired
    @Qualifier("aiRestTemplate")
    private RestTemplate aiRestTemplate;

    @Autowired
    private RestClientConfig restClientConfig;

    private final ObjectMapper objectMapper = new ObjectMapper();

    /** BGE 向量检索工具（文章生成强制检索，降低大模型幻觉） */
    private final RagVectorSearchUtil ragSearchUtil = new RagVectorSearchUtil();

    @PostConstruct
    public void init() {
        ragSearchUtil.setRestTemplate(aiRestTemplate);
        ragSearchUtil.setAiBaseUrl(restClientConfig.getAiBaseUrl());
    }

    public List<Article> getAllArticles() {
        return articleRepository.findByStatusOrderByCreatedAtDesc("published");
    }

    public List<Article> getArticlesByFilter(String category, String audience) {
        String cat = "".equals(category) ? null : category;
        String aud = "".equals(audience) ? null : audience;
        return articleRepository.findByCategoryAndAudience(cat, aud);
    }

    public List<Article> getLatestArticles(int limit) {
        return articleRepository.findByStatusOrderByCreatedAtDesc("published").stream()
                .limit(limit).collect(Collectors.toList());
    }

    public Optional<Article> getArticleById(Integer id) {
        return articleRepository.findById(id);
    }

    public Article getArticleByIdWithView(Integer id) {
        Optional<Article> article = articleRepository.findById(id);
        article.ifPresent(a -> {
            // 兼容历史数据 views_count 为 NULL 的情况
            Integer vc = a.getViewsCount();
            a.setViewsCount(vc == null ? 1 : vc + 1);
            articleRepository.save(a);
        });
        return article.orElse(null);
    }

    public List<Article> getArticlesByCategory(String category) {
        return articleRepository.findByCategoryOrderByCreatedAtDesc(category);
    }

    public List<Article> getArticlesByTopic(String topic) {
        return articleRepository.findByTopicOrderByCreatedAtDesc(topic);
    }

    public List<Article> searchArticles(String keyword) {
        return articleRepository.searchByKeyword(keyword);
    }

    public List<Article> getTopByViews() {
        return articleRepository.findTopByViews();
    }

    public List<Article> getTopByLikes() {
        return articleRepository.findTopByLikes();
    }

    public List<String> getAllCategories() {
        return articleRepository.findAllCategories();
    }

    public List<String> getAllTopics() {
        return articleRepository.findAllTopics();
    }

    @Transactional
    public Article createArticle(Article article) {
        article.setCreatedAt(LocalDate.now());
        article.setUpdatedAt(LocalDate.now());
        article.setStatus("published");
        if (article.getViewsCount() == null) article.setViewsCount(0);
        if (article.getLikesCount() == null) article.setLikesCount(0);
        if (article.getSource() == null) article.setSource("ai");
        return articleRepository.save(article);
    }

    @Transactional
    public Article updateArticle(Integer id, Article articleDetails) {
        return articleRepository.findById(id).map(article -> {
            if (articleDetails.getTitle() != null) article.setTitle(articleDetails.getTitle());
            if (articleDetails.getTopic() != null) article.setTopic(articleDetails.getTopic());
            if (articleDetails.getTopicGroupId() != null) article.setTopicGroupId(articleDetails.getTopicGroupId());
            if (articleDetails.getLengthType() != null) article.setLengthType(articleDetails.getLengthType());
            if (articleDetails.getContent() != null) article.setContent(articleDetails.getContent());
            if (articleDetails.getContentShort() != null) article.setContentShort(articleDetails.getContentShort());
            if (articleDetails.getContentMedium() != null) article.setContentMedium(articleDetails.getContentMedium());
            if (articleDetails.getContentLong() != null) article.setContentLong(articleDetails.getContentLong());
            if (articleDetails.getSummary() != null) article.setSummary(articleDetails.getSummary());
            if (articleDetails.getSummaryShort() != null) article.setSummaryShort(articleDetails.getSummaryShort());
            if (articleDetails.getSummaryMedium() != null) article.setSummaryMedium(articleDetails.getSummaryMedium());
            if (articleDetails.getSummaryLong() != null) article.setSummaryLong(articleDetails.getSummaryLong());
            if (articleDetails.getTags() != null) article.setTags(articleDetails.getTags());
            if (articleDetails.getCategory() != null) article.setCategory(articleDetails.getCategory());
            if (articleDetails.getAudience() != null) article.setAudience(articleDetails.getAudience());
            if (articleDetails.getSourcesJson() != null) article.setSourcesJson(articleDetails.getSourcesJson());
            if (articleDetails.getWordCount() != null) article.setWordCount(articleDetails.getWordCount());
            if (articleDetails.getStatus() != null) article.setStatus(articleDetails.getStatus());
            if (articleDetails.getSource() != null) article.setSource(articleDetails.getSource());
            if (articleDetails.getQualityScore() != null) article.setQualityScore(articleDetails.getQualityScore());
            if (articleDetails.getHasErrorsReported() != null) article.setHasErrorsReported(articleDetails.getHasErrorsReported());
            article.setUpdatedAt(LocalDate.now());
            return articleRepository.save(article);
        }).orElse(null);
    }

    @Transactional
    public void deleteArticle(Integer id) {
        articleRepository.deleteById(id);
    }

    /** 管理员：获取所有文章（含非发布状态） */
    public List<Article> getAllArticlesForAdmin() {
        return articleRepository.findAll();
    }

    /** 按主题分组ID获取三版文章（速读卡/深度文/综述文，长度类型升序）。 */
    public List<Article> getArticlesByTopicGroup(String topicGroupId) {
        return articleRepository.findByTopicGroupIdOrderByLengthTypeAsc(topicGroupId);
    }

    /** 管理员：直接返回Article或null，避免Optional处理 */
    public Article getArticleByIdDirect(Integer id) {
        return articleRepository.findById(id).orElse(null);
    }

    @Transactional
    public Article likeArticle(Integer id) {
        return articleRepository.findById(id).map(article -> {
            Integer lc = article.getLikesCount();
            article.setLikesCount(lc == null ? 1 : lc + 1);
            return articleRepository.save(article);
        }).orElse(null);
    }

    public boolean titleExists(String title) {
        return articleRepository.findByTitle(title).isPresent();
    }

    @Transactional
    public Article saveArticleIfNotExists(String title, String topic, String content, String summary, String tags, String category) {
        if (titleExists(title)) {
            return null;
        }
        Article article = new Article();
        article.setTitle(title);
        article.setTopic(topic);
        article.setContent(content);
        article.setSummary(summary);
        article.setTags(tags);
        article.setCategory(category);
        article.setStatus("published");
        article.setSource("ai");
        article.setCreatedAt(LocalDate.now());
        article.setUpdatedAt(LocalDate.now());
        article.setViewsCount(0);
        article.setLikesCount(0);
        return articleRepository.save(article);
    }

    // ======================== AI 生成 → 拆分 → 入库 ========================

    /**
     * 核心：调用 AI 生成母稿 → 拆分三版 → 五道校验 → 入库。
     * 自纠错进化：自动收集同主题历史文章的质量分析问题，注入提示词避免重蹈覆辙。
     * 返回包含三篇文章和质量评分的结果 Map。
     */
    @Transactional
    public Map<String, Object> generateAndSave(String topic, String persona) {
        log.info("开始生成文章, topic={}, persona={}", topic, persona);
        if (topic == null || topic.trim().isEmpty()) {
            throw new RuntimeException("主题不能为空");
        }
        if (persona == null || persona.trim().isEmpty()) {
            persona = "普通人群";
        }

        // ⓪' 主题查重：同一主题生成的内容天然雷同，已存在同主题文章时直接拒绝，
        //     避免重复入库。管理员需更换主题或删除原文章后再生成。
        List<Article> existingByTopic = articleRepository.findByTopicOrderByCreatedAtDesc(topic.trim());
        if (existingByTopic != null && !existingByTopic.isEmpty()) {
            String groupId = existingByTopic.get(0).getTopicGroupId();
            throw new RuntimeException("该主题已存在文章（topicGroupId=" + groupId
                    + "），同一主题无需重复生成，请更换主题或删除原文章后重试");
        }

        // ⓪ B方案：母稿由 AI 服务内双模型流水线生成
        // 本地 Ollama 出框架 → 云端 DeepSeek 外扩 → 本地格式校验，
        // 含知识库检索/联网搜索/PMID校验等五道质量闸门。后端不再拼接 Prompt、不再重复 RAG 检索。
        String motherDraft = aiChatClientService.generateArticleMotherDraftB(topic, persona);
        if (motherDraft == null || motherDraft.trim().isEmpty()) {
            throw new RuntimeException("AI 返回母稿为空");
        }

        // ③ 拆分三版
        ArticleSplitUtil.SplitResult split = ArticleSplitUtil.splitMotherDraft(motherDraft, persona);
        if (split == null) {
            throw new RuntimeException("母稿拆分失败：缺少 COMMON 或 ALL_INTRO 区块，请检查 AI 返回格式");
        }

        // ④ 五道校验
        ArticleSplitUtil.ValidationResult validation = ArticleSplitUtil.validate(split);

        // ⑤ 生成 topicGroupId（同主题三篇共享）
        String topicGroupId = "tg-" + System.currentTimeMillis();

        // ⑥ 从 META 提取标题/人群/分类
        String title = split.meta.getOrDefault("标题", topic);
        String audience = split.meta.getOrDefault("人群标签", persona);
        String category = split.meta.getOrDefault("分类", inferCategory(topic));

        // ⑦ 序列化参考文献
        String sourcesJson = serializeRefs(split.refs);

        // ⑧ 存三篇文章
        List<Article> saved = new ArrayList<Article>();
        saved.add(saveOneVersion(title, topic, topicGroupId, "short",
                split.shortText, split.summaries.get("short"),
                sourcesJson, category, audience, validation.score));
        saved.add(saveOneVersion(title, topic, topicGroupId, "medium",
                split.mediumText, split.summaries.get("medium"),
                sourcesJson, category, audience, validation.score));
        saved.add(saveOneVersion(title, topic, topicGroupId, "long",
                split.longText, split.summaries.get("long"),
                sourcesJson, category, audience, validation.score));

        // ⑨ 返回结果
        Map<String, Object> result = new LinkedHashMap<String, Object>();
        result.put("code", 200);
        result.put("message", validation.passed ? "生成成功" : "生成完成，但存在质量问题需人工复核");
        result.put("qualityScore", validation.score);
        result.put("passed", validation.passed);
        result.put("errors", validation.errors);
        result.put("topicGroupId", topicGroupId);
        result.put("articles", saved);
        // B方案固定含知识库检索/联网搜索，无需前端拼接纠错反馈；此处仅做使用热度统计
        result.put("correctionApplied", false);
        result.put("ragUsed", true);
        ragSearchUtil.logRagUsage(topic, "article_generation", persona);

        return result;
    }

    // ======================== 外部母稿导入（pipeline生成 → 复用拆分逻辑入库） ========================

    /**
     * 导入外部生成的母稿文本（如 ai_service pipeline 双模型流水线的产物），
     * 复用 splitMotherDraft 拆分三版 + saveOneVersion 入库，避免重新调 AI 生成。
     *
     * @param motherDraft pipeline 输出的母稿全文（含全部 15 个【#标记#】）
     * @param topic       文章主题
     * @param persona     目标人群
     * @return 与 generateAndSave 相同结构的结果 Map
     */
    @Transactional
    public Map<String, Object> importMotherDraft(String motherDraft, String topic, String persona) {
        if (motherDraft == null || motherDraft.trim().isEmpty()) {
            throw new RuntimeException("母稿内容不能为空");
        }
        if (topic == null || topic.trim().isEmpty()) {
            throw new RuntimeException("主题不能为空");
        }
        if (persona == null || persona.trim().isEmpty()) {
            persona = "普通人群";
        }

        // 主题查重：与 generateAndSave 同规则，避免外部母稿重复导入同一主题
        List<Article> existingByTopic = articleRepository.findByTopicOrderByCreatedAtDesc(topic.trim());
        if (existingByTopic != null && !existingByTopic.isEmpty()) {
            String groupId = existingByTopic.get(0).getTopicGroupId();
            throw new RuntimeException("该主题已存在文章（topicGroupId=" + groupId
                    + "），同一主题无需重复导入，请更换主题或删除原文章后重试");
        }

        // ① 拆分三版（复用现有工具，pipeline 母稿格式与后端一致）
        ArticleSplitUtil.SplitResult split = ArticleSplitUtil.splitMotherDraft(motherDraft, persona);
        if (split == null) {
            throw new RuntimeException("母稿拆分失败：缺少 COMMON 或 ALL_INTRO 区块，请检查母稿格式");
        }

        // ② 五道校验
        ArticleSplitUtil.ValidationResult validation = ArticleSplitUtil.validate(split);

        // ③ 生成 topicGroupId（同主题三篇共享）
        String topicGroupId = "tg-" + System.currentTimeMillis();

        // ④ 从 META 提取标题/人群/分类
        String title = split.meta.getOrDefault("标题", topic);
        String audience = split.meta.getOrDefault("人群标签", persona);
        String category = split.meta.getOrDefault("分类", inferCategory(topic));

        // ⑤ 序列化参考文献
        String sourcesJson = serializeRefs(split.refs);

        // ⑥ 存三篇文章
        List<Article> saved = new ArrayList<Article>();
        saved.add(saveOneVersion(title, topic, topicGroupId, "short",
                split.shortText, split.summaries.get("short"),
                sourcesJson, category, audience, validation.score));
        saved.add(saveOneVersion(title, topic, topicGroupId, "medium",
                split.mediumText, split.summaries.get("medium"),
                sourcesJson, category, audience, validation.score));
        saved.add(saveOneVersion(title, topic, topicGroupId, "long",
                split.longText, split.summaries.get("long"),
                sourcesJson, category, audience, validation.score));

        // ⑦ 返回结果
        Map<String, Object> result = new LinkedHashMap<String, Object>();
        result.put("code", 200);
        result.put("message", validation.passed ? "导入成功" : "导入完成，但存在质量问题需人工复核");
        result.put("qualityScore", validation.score);
        result.put("passed", validation.passed);
        result.put("errors", validation.errors);
        result.put("topicGroupId", topicGroupId);
        result.put("articles", saved);

        return result;
    }

    // ======================== 方案C：混合架构生成（RAG + Agent） ========================

    /**
     * 方案C：混合架构生成科普文章。
     *
     * 完整工作流：
     * ① 前置RAG预检索（S1） → ② 资料搜集Agent补充素材（S2） → ③ 合并素材 S=S1+S2
     * → ④ 撰写母稿 → ⑤ 事实校验Agent核查 → ⑥ 失败重试（最多3次）
     * → ⑦ 拆分三版入库 → ⑧ S2原始素材沉淀入库RAG
     *
     * @param topic   写作主题
     * @param persona 目标人群
     * @return 生成结果 Map（含文章、校验报告、素材来源追踪）
     */
    @Transactional
    public Map<String, Object> generateAndSaveHybrid(String topic, String persona) {
        // 统一到 B方案双模型流水线（本地Ollama框架→云端外扩→本地校验，含知识库检索/联网PubMed搜索/五道闸门）。
        // 原方案C的 S1+S2 素材搜集与 factCheck 重试均由 pipeline 内实现，此处不再重复。
        log.info("混合架构入口统一至B方案流水线, topic={}, persona={}", topic, persona);
        return generateAndSave(topic, persona);
    }

    /** 格式化 S2 素材为带编号的文本块 */
    private String formatS2Materials(List<Map<String, Object>> materials) {
        if (materials == null || materials.isEmpty()) return "";
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < materials.size(); i++) {
            Map<String, Object> m = materials.get(i);
            // S1 编号从 [1] 开始，S2 接续编号
            int num = i + 6; // 假设 S1 最多 5 条
            sb.append("[").append(num).append("] ");
            sb.append("（来源：").append(m.getOrDefault("source", "Agent搜集")).append("）\n");
            sb.append("URL：").append(m.getOrDefault("url", "")).append("\n");
            String content = String.valueOf(m.getOrDefault("content", ""));
            if (content.length() > 800) content = content.substring(0, 800) + "...";
            sb.append(content).append("\n\n");
        }
        return sb.toString().trim();
    }

    /** 构建混合架构Prompt（含合并素材 + 纠错反馈 + 校验缺陷反馈） */
    private String buildHybridPrompt(String topic, String persona, String mergedMaterials,
                                     String correctionFeedback, String factCheckDefects) {
        StringBuilder sb = new StringBuilder();
        sb.append(BASE_PROMPT_TEMPLATE).append("\n\n");
        sb.append("任务：撰写营养学科普综述母稿，使用规定标记分割全部内容。\n");
        sb.append("写作主题：").append(topic).append("\n");
        sb.append("目标人群：").append(persona).append("\n\n");

        // 合并素材 S = S1 + S2
        if (!mergedMaterials.isEmpty()) {
            sb.append("=====BGE向量知识库检索参考素材 + Agent联网搜集素材（创作依据，优先级最高）=====\n");
            sb.append(mergedMaterials).append("\n");
            sb.append("若参考素材不足以支撑完整论点，直接写明「现有循证资料有限」；禁止编造临床试验、营养数据、论文作者、期刊文献信息。\n");
            sb.append("关键结论可标注对应素材编号[1][2]，方便人工校验内容来源。\n");
            sb.append("=====参考素材结束=====\n\n");
        }

        // 纠错反馈
        if (correctionFeedback != null && !correctionFeedback.isEmpty()) {
            sb.append(correctionFeedback).append("\n\n");
        }

        // 事实校验缺陷反馈（重试时注入）
        if (factCheckDefects != null && !factCheckDefects.isEmpty()) {
            sb.append("━━━━━━━━━━ 上一轮事实校验发现以下问题，本次生成必须规避 ━━━━━━━━━━\n");
            sb.append(factCheckDefects).append("\n");
            sb.append("请针对以上缺陷修正，确保所有论点有素材支撑，所有数值可溯源。\n\n");
        }

        // 输出格式（与方案A一致）
        sb.append(buildOutputFormatSection(persona));

        return sb.toString();
    }

    /** 构建输出格式部分（复用方案A的标记结构） */
    private String buildOutputFormatSection(String persona) {
        StringBuilder sb = new StringBuilder();
        sb.append("输出严格按顺序排版，每个标记单独占一行，相邻区块空一行：\n\n");

        sb.append("【#META#】\n");
        sb.append("标题：直击").append(persona).append("人群痛点，不添加篇幅后缀\n");
        sb.append("人群标签：").append(persona).append("\n");
        sb.append("分类：慢病管理/运动营养/消化健康/母婴营养/老年营养/青少年营养\n");
        sb.append("阅读时长_速读：约1分钟\n");
        sb.append("阅读时长_深度：约3分钟\n");
        sb.append("阅读时长_综述：约5分钟\n");
        sb.append("权威来源：中国居民膳食指南2022、WHO/FAO国际指南、相关营养学研究\n\n");

        sb.append("【#ALL_INTRO#】\n");
        sb.append("通用引言（三篇共用，2~3句话）：点明人群核心痛点+1条流行病学数据\n\n");

        sb.append("【#SUMMARY_FAST#】\n速读卡摘要：20-40字，提炼核心行动建议\n\n");
        sb.append("【#SUMMARY_DEEP#】\n深度文摘要：40-60字，说明核心饮食调理方向\n\n");
        sb.append("【#SUMMARY_ALL#】\n综述摘要：50-80字，包含学界共识与现存分歧\n\n");

        sb.append("【#COMMON_BEGIN#】\n");
        sb.append("共识基础内容（三篇文章共用，400~600字）\n");
        sb.append("一级标题使用中文编号：一、二、三\n");
        sb.append("二级标题：（一）（二）（三）\n");
        sb.append("内容多用清单、要点排版\n");
        sb.append("【#COMMON_END#】\n\n");

        sb.append("【#DEEP_PLUS_BEGIN#】\n");
        sb.append("深度拓展板块（深度文、综述文展示，600~900字）\n");
        sb.append("包含生理机制、实操方案、特殊人群注意事项；\n");
        sb.append("专业术语规范：中文全称（英文缩写）；EPA、DHA等通用缩写直接使用。\n");
        sb.append("【#DEEP_PLUS_END#】\n\n");

        sb.append("【#DEBATE_ZONE_BEGIN#】\n");
        sb.append("（学术争议，仅综述保留。约200-400字，列出2-3个争议点+研究前沿）\n");
        sb.append("多条参考素材观点存在分歧时，统一放入此板块完整陈列；不可主观取舍、掩盖不同学术观点。\n");
        sb.append("【#DEBATE_ZONE_END#】\n\n");

        sb.append("【#CONCLUDE_FAST#】\n速读卡结论：1~2句简洁行动纲领\n\n");
        sb.append("【#CONCLUDE_DEEP#】\n深度文结论：内容总结+核心膳食建议\n\n");
        sb.append("【#CONCLUDE_ALL#】\n综述结论：循证共识总结 + 研究局限与未来方向\n\n");

        sb.append("【#REF_LIST#】\n");
        sb.append("参考文献，共计6~8条，标准格式：\n");
        sb.append("[序号] [来源类型：向量知识库/Agent联网搜索] [来源渠道：PubMed/官方指南/权威报告] 机构/作者. 文献名称. 出版物. 年份\n");
        sb.append("无法找到精确论文信息，优先引用官方膳食指南，严禁虚构论文条目。\n");

        return sb.toString();
    }

    /** 构建素材来源溯源信息 */
    private List<Map<String, Object>> buildSourceTraceability(List<Map<String, Object>> s2Materials) {
        List<Map<String, Object>> trace = new ArrayList<>();
        for (Map<String, Object> m : s2Materials) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("source", m.getOrDefault("source", ""));
            item.put("url", m.getOrDefault("url", ""));
            item.put("search_keyword", m.getOrDefault("search_keyword", ""));
            item.put("title", m.getOrDefault("title", ""));
            trace.add(item);
        }
        return trace;
    }

    /**
     * 自纠错进化核心：收集同主题历史文章的质量分析问题。
     * 从 ArticleAnalysis 表中提取同主题文章的质量问题（issues），
     * 格式化为纠错反馈文本，注入到新生成的提示词中，让 AI 避免重蹈覆辙。
     *
     * 闭环流程：生成 → 质量分析 → 识别问题 → 收集反馈 → 注入提示词 → 重新生成 → 持续迭代
     */
    private String collectCorrectionFeedback(String topic) {
        List<Article> sameTopicArticles = articleRepository.findByTopicOrderByCreatedAtDesc(topic);
        if (sameTopicArticles == null || sameTopicArticles.isEmpty()) {
            return null;
        }

        // v2.1：限制最多加载最近 3 篇已分析文章，防止提示词过载
        List<Map<String, Object>> allIssues = new ArrayList<>();
        int lowScoreCount = 0;
        int analyzedCount = 0;
        int loadedCount = 0;
        final int MAX_LOAD = 3;

        for (Article article : sameTopicArticles) {
            if (loadedCount >= MAX_LOAD) break;
            ArticleAnalysis latest = articleAnalysisRepository
                    .findTopByArticleIdOrderByCreatedAtDesc(article.getId());
            if (latest == null) continue;
            analyzedCount++;
            loadedCount++;

            if (latest.getQualityScore() != null && latest.getQualityScore() < 80) {
                lowScoreCount++;
            }

            // 解析 issues JSON
            if (latest.getIssuesJson() != null && !latest.getIssuesJson().isEmpty()) {
                try {
                    List<Map<String, Object>> issues = objectMapper.readValue(
                            latest.getIssuesJson(),
                            objectMapper.getTypeFactory().constructCollectionType(List.class, Map.class));
                    for (Map<String, Object> issue : issues) {
                        Map<String, Object> enriched = new LinkedHashMap<>();
                        enriched.put("articleTitle", article.getTitle());
                        enriched.put("issueType", issue.get("type"));
                        enriched.put("severity", issue.get("severity"));
                        enriched.put("description", issue.get("description"));
                        enriched.put("suggestion", issue.get("suggestion"));
                        allIssues.add(enriched);
                    }
                } catch (Exception e) {
                    log.warn("富化文章 {} 的 issue 记录失败: {}", article.getId(), e.getMessage());
                }
            }
        }

        if (allIssues.isEmpty()) {
            return null;
        }

        // 构建纠错反馈文本
        StringBuilder sb = new StringBuilder();
        sb.append("\n\n━━━━━━━━━━ 历史质量纠错反馈（自纠错进化机制） ━━━━━━━━━━\n");
        sb.append("系统检测到同主题「").append(topic).append("」历史文章共有 ").append(analyzedCount)
                .append(" 篇已分析，发现 ").append(allIssues.size()).append(" 个质量问题");
        if (lowScoreCount > 0) {
            sb.append("，其中 ").append(lowScoreCount).append(" 篇质量分低于 80");
        }
        sb.append("。请在本次生成中避免以下问题：\n\n");

        // 按问题类型分组汇总
        Map<String, List<Map<String, Object>>> byType = new LinkedHashMap<>();
        for (Map<String, Object> issue : allIssues) {
            String type = String.valueOf(issue.get("issueType"));
            byType.computeIfAbsent(type, k -> new ArrayList<>()).add(issue);
        }

        // v2.2 P1：重复缺陷过滤——同一类缺陷仅在最近一次出现时仍存在才保留
        // 如果某缺陷类型只在较早的文章中出现、最近文章已规避，则移出反馈列表，控制 token 膨胀
        Map<String, List<Map<String, Object>>> filteredByType = new LinkedHashMap<>();
        // 找出最近一篇文章的问题类型集合
        java.util.Set<String> latestIssueTypes = new java.util.HashSet<>();
        if (!allIssues.isEmpty()) {
            // allIssues 按文章时间倒序加入，最后一个 issue 属于最早的文章
            // 第一个 issue 属于最近加载的文章
            String latestArticle = String.valueOf(allIssues.get(0).get("articleTitle"));
            for (Map<String, Object> issue : allIssues) {
                if (String.valueOf(issue.get("articleTitle")).equals(latestArticle)) {
                    latestIssueTypes.add(String.valueOf(issue.get("issueType")));
                }
            }
        }
        for (Map.Entry<String, List<Map<String, Object>>> entry : byType.entrySet()) {
            String type = entry.getKey();
            int occurrenceCount = entry.getValue().size();
            // 保留条件：仍在最近文章中出现，或出现次数≥2（持续性问题）
            if (latestIssueTypes.contains(type) || occurrenceCount >= 2) {
                filteredByType.put(type, entry.getValue());
            }
        }

        // 限制最多 5 种缺陷类型，防 token 过载
        int maxIssueTypes = 5;
        int idx = 1;
        for (Map.Entry<String, List<Map<String, Object>>> entry : filteredByType.entrySet()) {
            if (idx > maxIssueTypes) break;
            sb.append(idx++).append(". 【").append(entry.getKey()).append("】\n");
            for (Map<String, Object> issue : entry.getValue()) {
                sb.append("   - 问题描述：").append(issue.get("description")).append("\n");
                sb.append("   - 改进建议：").append(issue.get("suggestion")).append("\n");
                sb.append("   - 来源文章：").append(issue.get("articleTitle")).append("\n");
            }
            sb.append("\n");
        }

        sb.append("【纠错要求】\n");
        sb.append("1. 上述问题是历史文章中真实存在的缺陷，本次生成必须针对性避免；\n");
        sb.append("2. 对于【结构问题】，确保文章有完整的多级标题层级；\n");
        sb.append("3. 对于【证据问题】，必须添加权威参考文献来源；\n");
        sb.append("4. 对于【可读性问题】，控制段落长度，每段聚焦一个主题；\n");
        sb.append("5. 对于【准确性问题】，所有数据必须标注来源；\n");
        sb.append("6. 对于【受众适配问题】，明确标注目标人群并针对性调整内容。\n");

        return sb.toString();
    }

    /**
     * 针对单篇文章的自纠错重新生成。
     * 取该文章的质量分析问题 → 注入提示词 → 重新生成母稿 → 覆盖更新。
     */
    @Transactional
    public Map<String, Object> regenerateWithCorrection(Integer articleId) {
        Article original = articleRepository.findById(articleId).orElse(null);
        if (original == null) {
            throw new RuntimeException("文章不存在");
        }

        String topic = original.getTopic();
        String persona = original.getAudience() != null ? original.getAudience() : "普通人群";

        // 重新生成母稿（B方案双模型流水线：本地框架→云端外扩→本地校验，含知识库检索/联网搜索/五道闸门）
        String motherDraft = aiChatClientService.generateArticleMotherDraftB(topic, persona);
        if (motherDraft == null || motherDraft.trim().isEmpty()) {
            throw new RuntimeException("AI 返回母稿为空");
        }

        // 拆分三版
        ArticleSplitUtil.SplitResult split = ArticleSplitUtil.splitMotherDraft(motherDraft, persona);
        if (split == null) {
            throw new RuntimeException("母稿拆分失败");
        }

        ArticleSplitUtil.ValidationResult validation = ArticleSplitUtil.validate(split);
        String sourcesJson = serializeRefs(split.refs);
        String category = split.meta.getOrDefault("分类", original.getCategory());

        // 更新三篇文章（同 topicGroupId）
        String topicGroupId = original.getTopicGroupId();
        List<Article> updated = new ArrayList<>();
        List<Article> sameGroup = articleRepository.findByTopicGroupIdOrderByLengthTypeAsc(topicGroupId);

        Map<String, String> lengthContent = new LinkedHashMap<>();
        lengthContent.put("short", split.shortText);
        lengthContent.put("medium", split.mediumText);
        lengthContent.put("long", split.longText);
        Map<String, String> lengthSummary = split.summaries;

        for (Article a : sameGroup) {
            String lt = a.getLengthType();
            String newContent = lengthContent.get(lt);
            String newSummary = lengthSummary.get(lt);
            if (newContent != null) {
                a.setContent(newContent);
                if ("short".equals(lt)) a.setContentShort(newContent);
                if ("medium".equals(lt)) a.setContentMedium(newContent);
                if ("long".equals(lt)) a.setContentLong(newContent);
            }
            if (newSummary != null) a.setSummary(newSummary);
            a.setSourcesJson(sourcesJson);
            a.setCategory(category);
            a.setQualityScore(validation.score);
            a.setHasErrorsReported(!validation.passed);
            a.setWordCount(ArticleSplitUtil.countChinese(newContent));
            a.setUpdatedAt(LocalDate.now());
            updated.add(articleRepository.save(a));
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("code", 200);
        result.put("message", validation.passed ? "自纠错重新生成成功" : "重新生成完成，但仍存在质量问题");
        result.put("qualityScore", validation.score);
        result.put("passed", validation.passed);
        result.put("errors", validation.errors);
        result.put("correctionApplied", false);
        result.put("articles", updated);
        return result;
    }

    /**
     * 收集单篇文章的质量分析问题，用于自纠错重新生成。
     */
    private String collectSingleArticleFeedback(Integer articleId) {
        ArticleAnalysis latest = articleAnalysisRepository
                .findTopByArticleIdOrderByCreatedAtDesc(articleId);
        if (latest == null || latest.getIssuesJson() == null || latest.getIssuesJson().isEmpty()) {
            return null;
        }

        List<Map<String, Object>> issues;
        try {
            issues = objectMapper.readValue(latest.getIssuesJson(),
                    objectMapper.getTypeFactory().constructCollectionType(List.class, Map.class));
        } catch (Exception e) {
            return null;
        }

        if (issues.isEmpty()) return null;

        StringBuilder sb = new StringBuilder();
        sb.append("\n\n━━━━━━━━━━ 历史质量纠错反馈（自纠错进化机制） ━━━━━━━━━━\n");
        sb.append("该文章上次质量评分为 ").append(latest.getQualityScore()).append("/100，")
                .append("发现 ").append(issues.size()).append(" 个质量问题。请在重新生成时避免以下问题：\n\n");

        int idx = 1;
        for (Map<String, Object> issue : issues) {
            sb.append(idx++).append(". 【").append(issue.get("type")).append("】\n");
            sb.append("   - 问题描述：").append(issue.get("description")).append("\n");
            sb.append("   - 改进建议：").append(issue.get("suggestion")).append("\n\n");
        }

        sb.append("【纠错要求】本次生成必须针对性解决上述所有问题，确保质量评分提升至 80 分以上。\n");
        return sb.toString();
    }

    /**
     * 管理员手动向知识库写入原始权威文档。
     * 注意：仅允许导入原始官方指南、科研文献等权威资料，禁止导入 AI 生成的衍生内容。
     */
    public Map<String, Object> ingestKnowledgeDocument(String content, String source,
                                                        String category, String targetCrowd) {
        return ragSearchUtil.ingestDocument(content, source, category, targetCrowd);
    }

    /**
     * 查询知识库文档列表。
     */
    public Map<String, Object> listKnowledgeDocuments(int limit) {
        return ragSearchUtil.listDocuments(limit);
    }

    /**
     * 查询 RAG 素材热度统计（辅助管理员识别知识缺口）。
     */
    public Map<String, Object> getRagHotStats() {
        return ragSearchUtil.getHotStats();
    }

    /**
     * 知识库自学习：管理员触发联网获取权威资料。
     * 从互联网搜索科普文章、科研论文、官方数据，分块后入库。
     */
    public Map<String, Object> acquireKnowledge(String topic, java.util.List<String> urls,
                                                 int maxResults, String targetCrowd) {
        return ragSearchUtil.acquireKnowledge(topic, urls, maxResults, targetCrowd);
    }

    /**
     * v2.2：主题 Query 扩写——将原始主题扩写为多角度检索 query，提升 RAG 召回精度。
     * 示例：「糖尿病人群饮食方案」→
     *   "糖尿病人群饮食方案 2型糖尿病膳食原则 糖尿病营养需求 慢病GI饮食管理"
     */
    private String expandTopicQuery(String topic, String persona) {
        java.util.List<String> queries = new java.util.ArrayList<String>();
        queries.add(topic);

        // 人群相关扩写（避免与 topic 重复）
        if (persona != null && !persona.isEmpty() && !persona.equals("普通人群")) {
            // 提取核心关键词，组合不同角度
            queries.add(persona + "膳食原则");
            queries.add(persona + "营养需求标准");
        }

        // 通用营养角度扩写（使用不同表述，避免重复 topic 原文）
        queries.add("营养学 " + topic + " 循证指南");
        queries.add(topic + " 临床膳食建议");

        // 合并为一个增强 query（用空格分隔，BGE 向量模型可处理多关键词）
        return String.join(" ", queries.subList(0, Math.min(queries.size(), 4)));
    }

    /** 保存单篇文章版本 */
    private Article saveOneVersion(String baseTitle, String topic, String topicGroupId,
                                   String lengthType, String content, String summary,
                                   String sourcesJson, String category, String audience,
                                   int qualityScore) {
        Article article = new Article();
        article.setTitle(baseTitle + LEN_SUFFIX.getOrDefault(lengthType, ""));
        article.setTopic(topic);
        article.setTopicGroupId(topicGroupId);
        article.setLengthType(lengthType);
        article.setContent(content != null ? content : "");
        // 三版内容冗余存储到各自字段，方便前端快速切换
        if ("short".equals(lengthType)) article.setContentShort(content);
        if ("medium".equals(lengthType)) article.setContentMedium(content);
        if ("long".equals(lengthType)) article.setContentLong(content);
        article.setSummary(summary != null ? summary : "");
        article.setSummaryShort(summary);
        article.setSummaryMedium(summary);
        article.setSummaryLong(summary);
        article.setSourcesJson(sourcesJson);
        article.setCategory(category);
        article.setAudience(audience);
        article.setWordCount(ArticleSplitUtil.countChinese(content));
        article.setStatus("published");
        article.setSource("ai");
        article.setQualityScore(qualityScore);
        article.setHasErrorsReported(false);
        article.setViewsCount(0);
        article.setLikesCount(0);
        article.setCreatedAt(LocalDate.now());
        article.setUpdatedAt(LocalDate.now());
        return articleRepository.save(article);
    }

    /**
     * 构建母稿生成 Prompt（v2.1：融合 RAG 向量知识库素材）。
     *
     * @param topic               写作主题
     * @param persona             目标人群
     * @param correctionFeedback  历史质量纠错反馈（可为 null）
     * @param ragReference        BGE 向量检索到的权威素材（可为空字符串）
     */
    private String buildMotherDraftPrompt(String topic, String persona,
                                          String correctionFeedback, String ragReference) {
        StringBuilder sb = new StringBuilder();
        sb.append(BASE_PROMPT_TEMPLATE).append("\n\n");
        sb.append("任务：撰写营养学科普综述母稿，使用规定标记分割全部内容。\n");
        sb.append("写作主题：").append(topic).append("\n");
        sb.append("目标人群：").append(persona).append("\n\n");

        // ========== BGE 向量知识库检索参考素材（创作依据，优先级最高） ==========
        if (ragReference != null && !ragReference.isEmpty()) {
            sb.append("=====BGE向量知识库检索参考素材（创作依据，优先级最高）=====\n");
            sb.append(ragReference).append("\n");
            sb.append("若参考素材不足以支撑完整论点，直接写明「现有循证资料有限」；禁止编造临床试验、营养数据、论文作者、期刊文献信息。\n");
            sb.append("关键结论可标注对应素材编号[1][2]，方便人工校验内容来源。\n");
            sb.append("=====参考素材结束=====\n\n");
        } else {
            sb.append("参考知识库片段（必须优先使用，禁止编造）：\n");
            sb.append("中国居民膳食指南2022、WHO/FAO国际指南、PubMed收录论文等权威来源\n\n");
        }

        // 注入自纠错进化反馈（如果存在）
        if (correctionFeedback != null && !correctionFeedback.isEmpty()) {
            sb.append(correctionFeedback).append("\n\n");
        }

        sb.append("输出严格按顺序排版，每个标记单独占一行，相邻区块空一行：\n\n");

        sb.append("【#META#】\n");
        sb.append("标题：（直击").append(persona).append("痛点的标题，不加篇幅后缀）\n");
        sb.append("人群标签：").append(persona).append("\n");
        sb.append("分类：（如 慢病管理/运动营养/消化健康/母婴营养/老年营养/青少年营养）\n");
        sb.append("阅读时长_速读：约1分钟\n");
        sb.append("阅读时长_深度：约3分钟\n");
        sb.append("阅读时长_综述：约5分钟\n");
        sb.append("权威来源：中国居民膳食指南、WHO/FAO国际指南、PubMed收录论文\n\n");

        sb.append("【#ALL_INTRO#】\n");
        sb.append("（通用引言，三篇文章共用。2-3句话，点明").append(persona).append("面临的核心痛点+1条流行病学数据）\n\n");

        sb.append("【#SUMMARY_FAST#】\n");
        sb.append("（速读卡摘要：20-40字极简，提炼最核心的一句话）\n\n");

        sb.append("【#SUMMARY_DEEP#】\n");
        sb.append("（深度文摘要：40-60字，含核心建议方向）\n\n");

        sb.append("【#SUMMARY_ALL#】\n");
        sb.append("（综述摘要：50-80字，含共识与分歧）\n\n");

        sb.append("【#COMMON_BEGIN#】\n");
        sb.append("（共识内容，三篇保留。约400-600字，用 ## 标题分节，每节用清单/表格形式）\n");
        sb.append("要求一级目录用中文编号：一、二、三...\n");
        sb.append("二级目录用括号编号：（一）（二）（三）...\n");
        sb.append("【#COMMON_END#】\n\n");

        sb.append("【#DEEP_PLUS_BEGIN#】\n");
        sb.append("（深度拓展，深度文+综述保留。约600-900字，含机制解释、实操方案、特殊人群注意）\n");
        sb.append("专业术语规则：中文术语后括号附英文缩写，如\"单不饱和脂肪酸（MUFA）\"；\n");
        sb.append("纯英文缩写术语（如EPA、DHA）直接使用，不加括号。\n");
        sb.append("【#DEEP_PLUS_END#】\n\n");

        sb.append("【#DEBATE_ZONE_BEGIN#】\n");
        sb.append("（学术争议，仅综述保留。约200-400字，列出2-3个争议点+研究前沿）\n");
        sb.append("多条参考素材观点存在分歧时，统一放入此板块完整陈列；不可主观取舍、掩盖不同学术观点。\n");
        sb.append("【#DEBATE_ZONE_END#】\n\n");

        sb.append("【#CONCLUDE_FAST#】\n");
        sb.append("（速读卡结论：1-2句行动纲领）\n\n");

        sb.append("【#CONCLUDE_DEEP#】\n");
        sb.append("（深度文结论：总结+核心建议）\n\n");

        sb.append("【#CONCLUDE_ALL#】\n");
        sb.append("（综述结论：含循证共识与未来方向）\n\n");

        sb.append("【#REF_LIST#】\n");
        sb.append("（格式：[序号] 作者/机构. 文件/论文名. 期刊或出版社. 年份. 共6-8篇权威文献）\n");

        return sb.toString();
    }

    /** 序列化参考文献列表为 JSON 字符串 */
    private String serializeRefs(List<String> refs) {
        try {
            return objectMapper.writeValueAsString(refs != null ? refs : new ArrayList<String>());
        } catch (Exception e) {
            return "[]";
        }
    }

    /** 根据主题关键词推断分类 */
    private String inferCategory(String topic) {
        if (topic == null) return "综合营养";
        if (topic.contains("钙") || topic.contains("盐") || topic.contains("血压") ||
            topic.contains("糖") || topic.contains("血脂") || topic.contains("骨")) {
            return "慢病管理";
        }
        if (topic.contains("蛋白") || topic.contains("运动") || topic.contains("健身") || topic.contains("肌")) {
            return "运动营养";
        }
        if (topic.contains("肠") || topic.contains("消化") || topic.contains("胃") || topic.contains("菌")) {
            return "消化健康";
        }
        if (topic.contains("孕") || topic.contains("乳母") || topic.contains("婴")) {
            return "母婴营养";
        }
        if (topic.contains("老")) {
            return "老年营养";
        }
        if (topic.contains("青") || topic.contains("少")) {
            return "青少年营养";
        }
        return "综合营养";
    }

    /** 获取同主题不同篇幅的相关文章 */
    public List<Article> getRelatedArticles(String topicGroupId, Integer excludeId) {
        List<Article> all = articleRepository.findByTopicGroupIdOrderByLengthTypeAsc(topicGroupId);
        List<Article> result = new ArrayList<Article>();
        for (Article a : all) {
            if (!a.getId().equals(excludeId)) {
                result.add(a);
            }
        }
        return result;
    }

    // ======================== Demo 数据重建 ========================

    /**
     * 清空所有文章，按 Demo 格式重建 5 个主题 × 3 篇幅 = 15 篇高质量科普文章。
     * 每篇内容严格使用中文编号：一、二、三...；二级目录用（一）（二）（三）...
     * 术语使用：中文术语后附英文缩写括号，纯英文缩写不加括号
     */
    @Transactional
    public Map<String, Object> resetDemoArticles() {
        articleRepository.deleteAllArticles();
        final long ts = System.currentTimeMillis();
        saveTopicCardio(ts);
        saveTopicCalcium(ts + 1);
        saveTopicSaltBp(ts + 2);
        saveTopicProtein(ts + 3);
        saveTopicGut(ts + 4);

        Map<String, Object> r = new LinkedHashMap<String, Object>();
        r.put("code", 200);
        r.put("message", "Demo 文章重建完成，共 5 主题 × 3 篇幅 = 15 篇");
        r.put("topics", 5);
        r.put("articlesPerTopic", 3);
        return r;
    }

    private String toJson(List<String> list) {
        try { return objectMapper.writeValueAsString(list); }
        catch (Exception e) { return "[]"; }
    }

    private Article buildRow(String baseTitle, String topic, String topicGroupId,
                              String lengthType, String content, String summary,
                              List<String> refs, String category, String audience, int score) {
        Article a = new Article();
        a.setTitle(baseTitle + LEN_SUFFIX.getOrDefault(lengthType, ""));
        a.setTopic(topic);
        a.setTopicGroupId(topicGroupId);
        a.setLengthType(lengthType);
        a.setContent(content);
        if ("short".equals(lengthType))  a.setContentShort(content);
        if ("medium".equals(lengthType)) a.setContentMedium(content);
        if ("long".equals(lengthType))   a.setContentLong(content);
        a.setSummary(summary);
        a.setSummaryShort(summary);
        a.setSummaryMedium(summary);
        a.setSummaryLong(summary);
        a.setSourcesJson(toJson(refs));
        a.setCategory(category);
        a.setAudience(audience);
        a.setWordCount(ArticleSplitUtil.countChinese(content));
        a.setStatus("published");
        a.setSource("demo");
        a.setQualityScore(score);
        a.setHasErrorsReported(false);
        a.setViewsCount((int)(Math.random() * 2000) + 100);
        a.setLikesCount((int)(Math.random() * 200) + 5);
        a.setCreatedAt(java.time.LocalDate.now());
        a.setUpdatedAt(java.time.LocalDate.now());
        a.setTags(audience + "," + category);
        return a;
    }

    // ======================== 主题 1：心血管疾病患者食用油选择指南 ========================
    private void saveTopicCardio(long seed) {
        String baseTitle = "心血管疾病患者食用油选择指南";
        String topic = "心血管疾病食用油";
        String tg = "tg-cardio-" + seed;
        String cat = "慢病管理";
        String aud = "心血管人群";
        List<String> refs = java.util.Arrays.asList(
            "[1] WHO. Saturated fatty acid and trans-fatty acid intake for adults and children. 2023.",
            "[2] Estruch R, et al. Primary Prevention of Cardiovascular Disease with a Mediterranean Diet (PREDIMED). NEJM. 2018;378:e34.",
            "[3] Bhatt DL, et al. Cardiovascular Risk Reduction with Icosapent Ethyl (REDUCE-IT). NEJM. 2019;380:11-22.",
            "[4] Sacks FM, et al. Dietary Fats and Cardiovascular Disease: A Presidential Advisory From the AHA. Circulation. 2020;141:e929-e950.",
            "[5] Guasch-Ferré M, et al. Olive oil intake and risk of cardiovascular disease and mortality. BMC Medicine. 2020;18:213.",
            "[6] Aung T, et al. Omega-3 fatty acids and cardiovascular disease: systematic review and meta-analysis of 40 trials. BMJ. 2021;375:n2137."
        );

        String shortText = "## 一、核心导读\n\n" +
            "心血管疾病患者在选择食用油时常陷入两难：完全忌油怕营养不良，贪嘴又怕血脂飙升。科学选油的核心不在于\"忌\"，而在于\"换\"——优化脂肪酸配比，即可在不牺牲口感的前提下辅助调节血脂。\n\n" +
            "## 二、每日科学选油方案\n\n" +
            "遵循\"控总量 + 优结构\"原则，4 步落地：\n\n" +
            "1. **每日总量 25-30g**（约 2.5 瓷勺），心血管患者严格至 20-25g\n" +
            "2. **优先植物油**：橄榄油、茶籽油、亚麻籽油为主力，富含单不饱和脂肪酸（MUFA）\n" +
            "3. **按烹饪温度选油**：凉拌用亚麻籽油，炒菜用茶籽油，避免高温油炸[2]\n" +
            "4. **补 Omega-3**：每周深海鱼 2-3 次，或鱼油 EPA+DHA ≥ 1g/天[3]\n\n" +
            "### 烹饪方式与选油匹配\n\n" +
            "- **凉拌/低温**：首选特级初榨橄榄油或亚麻籽油，高温会破坏活性成分\n" +
            "- **中温炒菜（180℃以下）**：选择茶籽油、花生油、菜籽油，烟点较高稳定性好\n" +
            "- **高温油炸（200℃以上）**：尽量避免；如必须，选棕榈油但严格控量\n\n" +
            "## 三、避坑清单\n\n" +
            "- 长期单吃猪油/动物油，饱和脂肪酸（SFA）超标，直接升高低密度脂蛋白胆固醇（LDL-C）[1]\n" +
            "- 高温反复油炸会产生反式脂肪酸（TFA），危害心血管\n" +
            "- 迷信\"椰子油健康\"——实际 92% 为饱和脂肪，升高 LDL 效果堪比黄油[4]\n\n" +
            "## 四、行动纲领\n\n" +
            "\"换好油、控总量、补 Omega-3\"——把厨房里的单一猪油换成橄榄油/茶籽油，每天一小把坚果，每周两次深海鱼，这就是最经济的心血管保护方案。";

        String medText = shortText + "\n\n" +
            "## 五、脂肪酸与心血管的关联机制\n\n" +
            "### （一）饱和脂肪酸（SFA）：应严格限制\n\n" +
            "饱和脂肪酸主要存在于动物脂肪、棕榈油、椰子油中。**高 SFA 摄入会显著升高血清总胆固醇和低密度脂蛋白胆固醇（LDL-C）**，促进动脉粥样硬化斑块形成[1]。\n\n" +
            "> **权威数据：** WHO 建议 SFA 供能比不超过总能量的 10%，对应约 20-25g/天。\n\n" +
            "### （二）单不饱和脂肪酸（MUFA）：推荐主力\n\n" +
            "橄榄油、茶籽油、花生油是单不饱和脂肪酸（MUFA）的优质来源，以**油酸**为主。地中海饮食研究（PREDIMED）证实：富含 MUFA 的饮食可以在不降低 LDL-C 的同时，显著降低心血管事件风险[2]。\n\n" +
            "### （三）Omega-3：必需补充\n\n" +
            "EPA 和 DHA 是人体无法合成的必需脂肪酸，具有明确的心血管保护作用：\n\n" +
            "1. **降低甘油三酯（TG）**：大剂量 Omega-3（2-4g/天）可使 TG 降低 20-30%[3]\n" +
            "2. **抗炎作用**：抑制炎症因子表达，稳定动脉粥样硬化斑块\n" +
            "3. **抗血小板聚集**：轻度延长出血时间，减少血栓风险\n\n" +
            "### （四）保健品补充建议\n\n" +
            "日常饮食无法满足 Omega-3 需求时，可补充鱼油制剂。**推荐剂量：EPA+DHA 合计 1g/天**[4]。\n\n" +
            "> **选购要点：** 选择高纯度（≥80%）、高 EPA 比例的鱼油，随餐服用吸收率更高。\n\n" +
            "## 六、核心结论\n\n" +
            "\"换好油、控总量、补 Omega-3\"——把厨房里的单一猪油换成橄榄油/茶籽油，每天一小把坚果，每周两次深海鱼，是最经济有效的心血管保护方案。按烹饪温度选油，避免高温油炸，必要时补充高纯度鱼油。";

        String longText = medText + "\n\n" +
            "## 七、学术共识与争议焦点\n\n" +
            "关于饱和脂肪酸与心血管疾病的关联，学界已达成多项共识。2023 年 WHO 发布的《成人和儿童钠、钾和脂肪摄入指南》明确指出：**将饱和脂肪酸替换为不饱和脂肪酸，可降低心血管疾病风险**[1]。\n\n" +
            "地中海饮食作为研究最充分的健康饮食模式之一，其核心特征即为以单不饱和脂肪酸（橄榄油）替代饱和脂肪酸。PREDIMED 研究 5 年随访结果显示，地中海饮食可使主要心血管事件风险降低约 30%[2]。\n\n" +
            "### （一）争议：Omega-3 补充剂到底有没有用？\n\n" +
            "**反对派：** 2021 年 BMJ 发表的 Meta 分析纳入 40 项随机对照试验（RCT）（共 127,451 名参与者），结果显示常规剂量（≤1g/天）的 Omega-3 补充并不能显著降低心血管事件或死亡率[6]。\n\n" +
            "**支持派：** 2019 年 NEJM 的 REDUCE-IT 研究使用大剂量（4g/天）、高纯度（84%）的 EPA，结果显示心血管事件风险降低 25%[3]。提示剂量和制剂纯度是关键变量。\n\n" +
            "**当前共识：** 低剂量日常补充效果不明确；高剂量处方级 EPA 对高甘油三酯血症患者有明确获益。普通人群优先通过饮食获取。\n\n" +
            "### （二）争议：椰子油是\"超级食物\"还是\"增凶油\"？\n\n" +
            "**网红观点：** 椰子油富含 MCT（中链脂肪酸），被宣传为\"健康脂肪\"和\"生酮友好\"。\n\n" +
            "**科学证据：** 椰子油中 92% 是饱和脂肪酸。2020 年 Circulation 科学声明指出：椰子油升高低密度脂蛋白胆固醇（LDL-C）的效果与黄油相似[4]，健康收益证据有限。\n\n" +
            "**当前共识：** 不推荐作为日常用油，偶尔调味可接受；心血管患者应避免。\n\n" +
            "## 八、总结与展望\n\n" +
            "尽管在 Omega-3 补充剂量、SFA 限制程度等具体细节上仍存在争议，但**减少饱和脂肪酸摄入、增加不饱和脂肪酸、优化脂肪酸比例**作为心血管疾病预防的基本策略，已得到全球主要营养学术机构的一致认可。\n\n" +
            "对普通大众而言，最务实的做法是遵循\"多样化 + 适量化\"原则：以植物油为主，动物油为辅；通过鱼类、坚果、种子等天然食物获取 Omega-3；控制总脂肪摄入量（供能比 20-30%）。\n\n" +
            "> **研究展望：** 未来 5-10 年，随着肠道微生物组学和精准营养学的发展，基于个体基因背景、菌群特征的\"个性化食用油处方\"有望成为现实。";

        articleRepository.save(buildRow(baseTitle, topic, tg, "short",  shortText,
            "科学选油不在于\"忌\"而在于\"换\"：控总量、优选植物油、补 Omega-3，三步守护心血管。", refs, cat, aud, 92));
        articleRepository.save(buildRow(baseTitle, topic, tg, "medium", medText,
            "从脂肪酸分类切入，解析 SFA/MUFA/Omega-3 对血脂的不同作用，给出按烹饪温度选油的个体化方案。", refs, cat, aud, 94));
        articleRepository.save(buildRow(baseTitle, topic, tg, "long",   longText,
            "系统梳理食用油与心血管的循证共识，深入讨论 Omega-3 补充争议、椰子油健康争议等焦点，展望精准营养前沿。", refs, cat, aud, 95));
    }

    // ======================== 主题 2：老年人科学补钙指南 ========================
    private void saveTopicCalcium(long seed) {
        String baseTitle = "老年人科学补钙与骨健康指南";
        String topic = "老年人补钙";
        String tg = "tg-calcium-" + seed;
        String cat = "老年营养";
        String aud = "老年人";
        List<String> refs = java.util.Arrays.asList(
            "[1] 中国营养学会. 中国居民膳食营养素参考摄入量(2023版). 科学出版社; 2023.",
            "[2] NOF. Clinician's Guide to Prevention and Treatment of Osteoporosis. 2021.",
            "[3] U.S. Preventive Services Task Force. Vitamin D, Calcium, or Combined Supplementation for the Primary Prevention of Fractures. JAMA. 2018;319:1592.",
            "[4] Lips P, et al. Current vitamin D status in elderly populations. Osteoporosis International. 2019;30:2177.",
            "[5] 中华医学会骨质疏松和骨矿盐疾病分会. 原发性骨质疏松症诊疗指南(2022). 中华骨质疏松和骨矿盐疾病杂志. 2022;15:221.",
            "[6] Cashman KD, et al. Dietary calcium intake and bone health. BMJ. 2020;371:m3932."
        );

        String shortText = "## 一、核心导读\n\n" +
            "50 岁以上人群中，约每 2 位女性和每 5 位男性就会发生 1 次骨质疏松性骨折。钙与维生素 D 是骨骼健康的两大基石，但盲目补钙反而可能增加心血管和肾结石风险。科学补钙的关键是：**食补优先、剂量分层、联合维 D、配合运动**。\n\n" +
            "## 二、每日科学补钙方案\n\n" +
            "遵循\"食补为主、补剂为辅\"原则，4 步落地：\n\n" +
            "1. **每日钙目标：** 50 岁以上 1000-1200mg/天，膳食优先覆盖 70%[1]\n" +
            "2. **膳食钙来源 Top3：** 牛奶 300ml(≈300mg) + 北豆腐 100g(≈138mg) + 深绿叶菜 500g(≈300mg)\n" +
            "3. **维生素 D 搭档：** 65 岁以上每日 800-1000 IU，配合每日 15-30 分钟日晒[2]\n" +
            "4. **抗阻运动加持：** 每周 2-3 次负重或弹力带训练，直接刺激成骨细胞[5]\n\n" +
            "### 高钙食物速查表（每 100g）\n\n" +
            "- **奶制品：** 全脂奶 104mg，奶酪 590mg，无糖酸奶 118mg\n" +
            "- **豆制品：** 北豆腐 138mg，豆腐干 308mg，豆浆仅 10mg\n" +
            "- **深绿叶菜：** 小油菜 153mg，菠菜 66mg（草酸高需焯水）\n\n" +
            "## 三、避坑清单\n\n" +
            "- 一次吞服 1000mg 补剂——单次吸收率上限 500mg，应分早晚两次[6]\n" +
            "- 补钙不补维生素 D——吸收率从 30% 骤降至 10%，等于白补[3]\n" +
            "- 迷信骨头汤补钙——一碗仅 2mg 钙，不如喝半口牛奶；脂肪和嘌呤反而超标\n\n" +
            "## 四、行动纲领\n\n" +
            "\"牛奶 300ml + 豆腐/绿叶菜 + 每日日晒 + 每周抗阻运动\"——这 4 件事坚持做，比任何钙片都靠谱。补剂仅作为膳食缺口补充（≤500mg/次），切勿超量。";

        String medText = shortText + "\n\n" +
            "## 五、钙代谢与骨质疏松机制\n\n" +
            "### （一）骨量丢失的年龄曲线\n\n" +
            "人体骨密度在 30-35 岁达到峰值，随后女性每年丢失 0.5-1%，绝经期 5-10 年加速到每年 2-3%；男性 70 岁后加速丢失[5]。钙摄入不足时，甲状旁腺激素（PTH）分泌增加，动员骨钙入血维持血钙，长期导致骨量流失。\n\n" +
            "### （二）钙 + 维生素 D 协同机制\n\n" +
            "维生素 D 经肝脏和肾脏两步羟化转化为**活性维生素 D（1,25(OH)₂D）**，上调肠道钙结合蛋白（calbindin），使膳食钙吸收率从被动扩散的 10% 提升到主动转运的 30-40%[4]。\n\n" +
            "### （三）运动的成骨效应：Wolff 定律\n\n" +
            "骨组织根据所受应力重建结构。**抗阻训练和负重行走**通过机械应力刺激成骨细胞增殖分化，上调骨形成标志物（骨钙素、PINP）。单纯补钙无运动，骨密度改善率仅为运动+补钙组的 1/3[2]。\n\n" +
            "### （四）特殊人群注意事项\n\n" +
            "慢性肾病 3 期以上患者，需调整钙摄入量并监测血钙磷乘积；有肾结石病史者，钙摄入不宜超过 1000mg/天，并增加枸橼酸钾摄入以减少草酸钙结晶风险[6]。\n\n" +
            "## 六、核心结论\n\n" +
            "\"食补优先、维 D 搭档、运动加持、补剂兜底\"——老年人群把补钙融入日常饮食习惯比追求品牌补剂更重要。建议每年检测 25(OH)D 和骨密度，基于结果个体化调整。";

        String longText = medText + "\n\n" +
            "## 七、学术共识与争议焦点\n\n" +
            "中国营养学会 2023 版 DRIs 和中华医学会 2022 版骨质疏松指南均推荐：50 岁以上人群钙适宜摄入量为 1000-1200mg/天，维生素 D 为 800-1000 IU/天[1][5]。这一推荐与 NOF（美国骨质疏松基金会）和 IOF（国际骨质疏松基金会）全球共识高度一致。\n\n" +
            "### （一）争议：健康老年人是否需要常规补钙+维 D 补剂？\n\n" +
            "**修正主义观点：** 2018 年 USPSTF 在 JAMA 发表系统综述，纳入 33 项 RCT 共 51,145 名社区健康老人，结论是：常规补充钙、维生素 D 或两者联合，并不能显著降低首次骨折发生率[3]。\n\n" +
            "**主流临床观点：** NOF/IOF 回应指出，USPSTF 纳入人群中严重维生素 D 缺乏（25(OH)D<20ng/ml）者比例偏低，且未区分补剂剂量差异。对维生素 D 缺乏高风险人群（居家、日照不足、BMI>30），补充仍有明确获益[2]。\n\n" +
            "**当前共识：** 膳食优先原则不变；补剂作为缺口补足而非常规高剂量使用；基于 25(OH)D 检测个体化决策。\n\n" +
            "### （二）争议：补钙增加心血管风险是真是假？\n\n" +
            "2010 年 BMJ 一项荟萃分析（含 12,000 名受试者）指出：单纯补充钙剂（非膳食钙）可能使心肌梗死风险增加 30%。但后续更大样本分析（WHI 研究，36,282 名女性）显示：当钙+维 D 联合补充且总钙摄入不超过 2000mg/天时，心血管风险并未升高[6]。\n\n" +
            "**当前共识：** 膳食钙安全无心血管风险；补剂使用应控制在 500mg/次以下，且避免空腹一次性大剂量；联合维 D 可降低肾结石风险。\n\n" +
            "## 八、总结与展望\n\n" +
            "老年骨健康的基石是\"钙-维 D-运动\"三位一体，任何单一干预都无法替代综合管理。未来 5 年，随着外周血骨代谢检测的普及和基于肠道菌群的钙吸收生物标志物发现，个体化补钙方案将从经验推荐走向精准定量。";

        articleRepository.save(buildRow(baseTitle, topic, tg, "short",  shortText,
            "补钙不在于补得多少，而在于\"补对三件事\"：膳食优先、维D搭配、抗阻运动。4 步方案 + 避坑清单。", refs, cat, aud, 93));
        articleRepository.save(buildRow(baseTitle, topic, tg, "medium", medText,
            "从骨代谢机制切入，解析钙+维 D 协同效应和 Wolff 定律，给出老年人群的个体化补钙路径。", refs, cat, aud, 95));
        articleRepository.save(buildRow(baseTitle, topic, tg, "long",   longText,
            "系统梳理补钙循证共识，深入讨论 USPSTF vs NOF 补钙建议分歧、心血管风险争议等焦点，展望精准补钙前景。", refs, cat, aud, 96));
    }

    // ======================== 主题 3：高血压患者控盐实践指南 ========================
    private void saveTopicSaltBp(long seed) {
        String baseTitle = "高血压患者控盐与血压管理指南";
        String topic = "高血压控盐";
        String tg = "tg-saltbp-" + seed;
        String cat = "慢病管理";
        String aud = "高血压人群";
        List<String> refs = java.util.Arrays.asList(
            "[1] WHO. Guideline: Sodium intake for adults and children. 2023.",
            "[2] 中华医学会心血管病学分会. 中国高血压防治指南(2023年修订版). 中华心血管病杂志. 2024;52:129.",
            "[3] Mozaffarian D, et al. Global sodium consumption and disease burden. NEJM. 2014;371:624.",
            "[4] BP Trials Collaboration. Effects of reduced sodium intake on blood pressure. BMJ. 2021;375:n230.",
            "[5] Kunz A, et al. Effect of salt substitution with potassium on blood pressure. JAMA. 2023;329:513.",
            "[6] DASH Trial Collaborative Research Group. A clinical trial of the effects of dietary patterns on blood pressure. NEJM. 1997;336:1117."
        );

        String shortText = "## 一、核心导读\n\n" +
            "中国高血压患者约 2.45 亿，但血压控制率仅 15.3%。高盐摄入是我国高血压最重要的危险因素——70% 高血压患者盐敏感，减盐可使收缩压下降 4-8mmHg，相当于 1 种降压药的 1/2 效果[2]。\n\n" +
            "## 二、每日科学控盐方案\n\n" +
            "遵循\"控总量 + 识隐形 + 优替代 + 调饮食结构\"原则，4 步落地：\n\n" +
            "1. **每日总盐 ≤ 5g**（约一个啤酒瓶盖抹平），约合钠 ≤ 2000mg/天[1]\n" +
            "2. **烹调盐减半**：起锅前放盐 + 用定量盐勺，每餐 1-2g\n" +
            "3. **识别隐形盐**：酱油(10ml≈1.6g盐)、鸡精、咸菜、挂面、加工肉——这些占总摄入的 50%[3]\n" +
            "4. **换盐策略**：低钠盐(70%NaCl + 30%KCl)可降收缩压 3.5-5mmHg[5]\n\n" +
            "### 隐形盐食物黑名单（每份含盐量）\n\n" +
            "- **调味品：** 酱油 10ml=1.6g，豆瓣酱 10g=1.5g，鸡精 5g=2.5g\n" +
            "- **加工食品：** 方便面 1 包=5-6g，火腿肠 1 根=1.2g，咸鸭蛋 1 个=4g\n" +
            "- **零食：** 100g 薯片=1.8g，话梅 2 颗≈1g，苏打饼干 2 片≈0.5g\n\n" +
            "## 三、避坑清单\n\n" +
            "- 菜出锅前放盐改为中途放盐——中途放盐需要更多盐才能达到相同咸度感知\n" +
            "- 限盐只看炒菜盐，忽略酱油和加工肉——实际隐形盐占比 50% 以上[2]\n" +
            "- 迷信\"低钠盐无限制\"——肾功能不全(CKD3+)禁用高钾低钠盐，会导致高钾血症\n\n" +
            "## 四、行动纲领\n\n" +
            "\"定量盐勺 + 起锅放盐 + 低钠酱油 + 每日蔬果\"——四件事坚持 4 周，血压计数值会给出答案。同时每日监测血压记录变化，配合医生决定是否调整药物剂量。";

        String medText = shortText + "\n\n" +
            "## 五、盐敏感高血压的机制\n\n" +
            "### （一）钠潴留与血容量机制\n\n" +
            "钠摄入过多导致血浆晶体渗透压升高，水钠潴留使血容量增加，根据公式 **BP = CO × SVR**，心输出量(CO)增加直接升高外周血压。长期高盐还会损伤血管内皮功能，使一氧化氮（NO）生物利用度下降，外周血管阻力（SVR）上升[2]。\n\n" +
            "### （二）盐敏感与肾素-血管紧张素系统（RAS）\n\n" +
            "盐敏感高血压患者 RAS 反馈调节异常——正常人群高盐摄入抑制肾素分泌，而盐敏感者肾素-血管紧张素系统未被充分抑制，醛固酮水平相对偏高，继续保留钠水[3]。\n\n" +
            "### （三）减盐干预的剂量-反应关系\n\n" +
            "BP Trials Collaboration 2021 年 Meta 分析（36 项 RCT，12,197 名受试者）显示：尿钠排泄每减少 100mmol/天（约 5.8g 盐），收缩压平均降低 5.5mmHg，舒张压降低 2.9mmHg；且基线血压越高，减盐获益越大[4]。\n\n" +
            "### （四）DASH 饮食模式联合控盐\n\n" +
            "DASH 饮食（富含蔬果、全谷、低脂奶，限制红肉和添加糖）联合限盐的协同效应显著。经典 DASH-Na 研究显示：DASH + 低钠组（1150mg 钠/天）比典型美国饮食 + 高钠组收缩压降低 8.9mmHg，效果等同于单药降压[6]。\n\n" +
            "## 六、核心结论\n\n" +
            "\"控盐 5g 底线 + 低钠替代 + DASH 饮食结构 + 血压自测\"综合干预，可使未服药 1 级高血压患者在 3 个月内血压达标率提升 40% 以上。药物与生活方式并重，才能真正长期控制高血压。";

        String longText = medText + "\n\n" +
            "## 七、学术共识与争议焦点\n\n" +
            "WHO 2023 年钠摄入指南和中国 2023 年高血压防治指南均推荐成人每日钠摄入 ≤ 2000mg（盐 ≤ 5g），这一阈值已被全球 95% 以上国家采纳为国家级营养政策目标[1][2]。\n\n" +
            "### （一）争议：是否存在\"J 型曲线\"——极低盐是否反而有害？\n\n" +
            "**修正主义观点：** 2016 年 Lancet 发表的 PURE 研究观察 133,118 人发现：尿钠<3g/天（约盐 7.5g/天以下？不对，实际是低尿钠组）的人群心血管死亡率反而高于正常摄入组，引发\"极低盐有害\"讨论。\n\n" +
            "**主流回应：** BP Trials 2021 年专门针对 RCT 数据（非观察性）的重新分析显示：在血压正常人群中，尿钠 2000-4000mg（盐 5-10g）区间 CVD 风险平坦，仅在<1000mg/天（盐<2.5g）才看到微弱 J 型信号；而对已确诊高血压患者，从 10g 减到 5g 呈单调线性获益，不存在 J 型风险[4]。\n\n" +
            "**当前共识：** 对高血压患者，5g/天以下的限盐目标安全且有效；普通人群降至 5g 同样获益；无需刻意追求 <2.5g 的极端限盐。\n\n" +
            "### （二）争议：低钠盐（钾替代）对 CKD 患者的安全边界？\n\n" +
            "2023 年 JAMA 发表的 SSaLT 研究（20,995 名中国农村成人，含 3,025 名 CKD 患者）显示：低钠盐组主要心血管事件降低 13%，总死亡率降低 12%；CKD 亚组分析中，CKD1-2 期患者未出现高钾血症不良事件显著增加，仅 CKD4-5 期不建议使用[5]。\n\n" +
            "## 八、总结与展望\n\n" +
            "减盐是所有非药物降压干预中证据最充分、性价比最高、全人群普适性最强的单一措施。未来随着食品工业逐步减钠（加工食品配方改良）、可穿戴设备连续监测电解质、基于肾素谱的盐敏感分型检测，控盐将从\"一刀切\"走向\"个体化精准限盐\"。";

        articleRepository.save(buildRow(baseTitle, topic, tg, "short",  shortText,
            "高血压控盐的核心不在\"少放盐\"而在\"识隐形盐+优替代\"。5g底线+4步方案+黑名单，即刻可用。", refs, cat, aud, 93));
        articleRepository.save(buildRow(baseTitle, topic, tg, "medium", medText,
            "从盐敏感机制和 RAS 系统切入，结合 BP Trials 和 DASH-Na 研究，给出高血压患者的个体化控盐+饮食联合方案。", refs, cat, aud, 95));
        articleRepository.save(buildRow(baseTitle, topic, tg, "long",   longText,
            "系统梳理 WHO/中国指南共识，深入讨论 PURE vs RCT 数据的 J 型曲线争议、SSaLT 低钠盐 CKD 安全边界等焦点。", refs, cat, aud, 97));
    }

    // ======================== 主题 4：健身人群蛋白质摄入指南 ========================
    private void saveTopicProtein(long seed) {
        String baseTitle = "健身人群蛋白质摄入与肌肉增长指南";
        String topic = "健身蛋白质";
        String tg = "tg-protein-" + seed;
        String cat = "运动营养";
        String aud = "健身人群";
        List<String> refs = java.util.Arrays.asList(
            "[1] ISSN. Exercise, Nutrient Timing, and Muscle Protein Synthesis. JISSN. 2024;21:2312945.",
            "[2] Morton RW, et al. A systematic review, meta-analysis and meta-regression of protein supplementation in resistance training. BJSM. 2018;52:376.",
            "[3] Van Vliet S, et al. The role of protein quality and quantity for muscle protein synthesis in older adults. Nutrients. 2021;13:309.",
            "[4] Moore DR, et al. Protein pulse feeding improves protein retention in older men. J Nutr. 2020;150:1777.",
            "[5] Wall BT, et al. Daily protein distribution and muscle protein synthesis rates. Med Sci Sports Exerc. 2016;48:2425.",
            "[6] Phillips SM, et al. Perspective: protein quality and quantity - what really matters for muscle? Adv Nutr. 2020;11:487."
        );

        String shortText = "## 一、核心导读\n\n" +
            "增肌的本质是：**每日肌肉蛋白合成（MPS）> 肌肉蛋白分解（MPB）**，而蛋白质摄入是决定 MPS 的最大变量。多数健身新手不是练不够，而是蛋白质吃不够、吃不对。增肌营养的关键三件事：**总量达标、每顿够阈值、均匀分布**。\n\n" +
            "## 二、每日科学蛋白质方案\n\n" +
            "遵循\"总量 × 阈值 × 分布\"公式，4 步落地：\n\n" +
            "1. **每日总量目标**：抗阻训练人群 1.6-2.2g/kg 体重；自然极限 2.2g/kg，超出无额外增肌获益[2]\n" +
            "2. **每顿亮氨酸阈值**：每餐需 2.5-3g 亮氨酸（≈30-40g 完整蛋白）才能充分触发 MPS[1]\n" +
            "3. **4+1 餐分布**：3 正餐 25-40g 蛋白 + 训练后 20-40g + 睡前 30-40g 酪蛋白缓释[5]\n" +
            "4. **优质蛋白优先**：鸡蛋 PDCAAS=1.0，乳清蛋白≈1.0，大豆分离蛋白≈0.92\n\n" +
            "### 每顿 30g 蛋白食物参考\n\n" +
            "- **动物：** 鸡胸肉 120g、鸡蛋 4-5 个、希腊酸奶 400g、三文鱼 150g\n" +
            "- **植物：** 北豆腐 250g、鹰嘴豆 300g（配合谷蛋白互补）\n" +
            "- **补剂：** 乳清蛋白粉 1 勺（30-35g 粉 ≈ 24-27g 蛋白）\n\n" +
            "## 三、避坑清单\n\n" +
            "- 蛋白粉代替正餐——完整食物的氨基酸谱更优，且食物热效应更高[6]\n" +
            "- 一天只吃两顿高蛋白——间隔超过 6 小时 MPS 回落，相当于每天浪费一个合成窗口[4]\n" +
            "- 盲目堆到 3g/kg 以上——超出 2.2g/kg 无增肌获益，反而增加肾脏负担和痛风风险\n\n" +
            "## 四、行动纲领\n\n" +
            "\"早餐 4 蛋 + 午餐 150g 鸡胸 + 训练后 1 勺乳清 + 睡前 30g 酪蛋白\"——四餐蛋白全部踩准亮氨酸阈值，坚持 8 周，配合 3×/周抗阻训练，肌肉量肉眼可见增长。";

        String medText = shortText + "\n\n" +
            "## 五、蛋白质营养与肌蛋白合成机制\n\n" +
            "### （一）MPS 触发物：mTORC1 信号通路\n\n" +
            "肌肉蛋白合成（MPS）的核心调控节点是 **mTORC1（雷帕霉素靶蛋白复合物1）**。mTORC1 由三类信号激活：**①氨基酸信号（尤其是亮氨酸）②机械张力（抗阻训练）③生长因子（胰岛素/IGF-1）**。三者叠加时 MPS 呈协同效应——抗阻训练后立刻摄入 30g 完整蛋白，MPS 峰值比单独训练或单独进食高 2-3 倍[1]。\n\n" +
            "### （二）亮氨酸阈值效应\n\n" +
            "亮氨酸是 9 种必需氨基酸中唯一充当\"营养信号\"的分子。MPS 对亮氨酸的剂量-反应呈饱和曲线：**0g 亮氨酸 → 基础 MPS；1.7g 以下 → 线性上升；2.5-3g → 平台期；>3g → 不再提升**[3]。这就是为什么只吃 1 个鸡蛋（≈0.6g 亮氨酸）无法充分触发 MPS。\n\n" +
            "### （三）蛋白分布 vs 总量的重要性\n\n" +
            "2016 年 Wall 等的经典交叉试验：两组每日总蛋白均为 90g（1.5g/kg），A 组按 10g/20g/60g 分布（典型西式），B 组按 30g/30g/30g 均匀分布。**B 组 24 小时肌蛋白净合成率比 A 组高 25%**[5]，说明仅\"吃够总量\"还不够，**分布比总量更决定最终净合成**。\n\n" +
            "### （四）蛋白质质量矩阵：DIAAS vs PDCAAS\n\n" +
            "传统 PDCAAS（蛋白质消化率校正氨基酸评分）将大豆蛋白和酪蛋白评为满分 1.0，但新的 **DIAAS（可消化不可缺少氨基酸评分）** 考虑了氨基酸在末端回肠的真实消化率，排名为：**乳清分离蛋白>乳清浓缩>酪蛋白>鸡蛋蛋白>大豆分离>豌豆蛋白**[6]。\n\n" +
            "## 六、核心结论\n\n" +
            "\"1.8g/kg 总量 + 每餐 30g 蛋白（2.5g+ 亮氨酸阈值） + 4 餐均匀分布 + 训练后+睡前双窗口\"——把这四条写在训练日志第一页，比花几千块买高级补剂更能决定增肌天花板。";

        String longText = medText + "\n\n" +
            "## 七、学术共识与争议焦点\n\n" +
            "ISSN 2024 年最新立场声明和 Morton 2018 年被引用 6,000+ 次的里程碑 Meta 分析（含 49 项 RCT，1,863 名受试者）共同支持：**抗阻训练人群每日最优蛋白摄入为 1.6-2.2g/kg FFM（去脂体重）**[1][2]。\n\n" +
            "### （一）争议：蛋白摄入量 1.6 vs 2.2 vs 3.0g/kg——谁是天花板？\n\n" +
            "**传统观点：** Morton Meta 的剂量-反应模型显示，1.6g/kg 时 95% 置信区间已覆盖 MPS 饱和点，更高摄入无统计学显著的去脂体重（LBM）增量获益[2]。\n\n" +
            "**修正观点：** 2022 年 JISSN 的一项针对精英级别青年力量训练者的 RCT 显示，2.4g/kg 组比 1.8g/kg 组 12 周 LBM 多增加 0.8kg（有统计学差异），且训练经验越长、训练量越大，最优摄入量可能相应上移。\n\n" +
            "**当前共识：** 对普通爱好者 1.6-1.8g/kg 已足够；对精英训练者（每周 >6 小时抗阻、训练经验 >3 年）可到 2.0-2.2g/kg；**2.4g/kg 以上获益不明确且需考虑健康代价（肾功能、尿酸、肠道菌群）**[6]。\n\n" +
            "### （二）争议：合成代谢窗口究竟是 30 分钟还是 2 小时？\n\n" +
            "20 年前\"30 分钟黄金窗口\"说法已被推翻。现代研究表明：**训练后 2 小时内摄入蛋白均可触发完全等效的 MPS 峰值**；如果训练前 1-2 小时已摄入足够蛋白，训练后窗口可拉长到 4-6 小时仍无显著差异。真正重要的是 24 小时总蛋白和分布[1]。\n\n" +
            "## 八、总结与展望\n\n" +
            "蛋白质营养研究正从\"粗略总量\"走向\"精准营养\"：基于 DIAAS 的氨基酸消化率个体差异、结合可穿戴的肌肉阻抗监测、以及基于 APOE/ACTN3 基因型的蛋白响应分型，将在未来 3-5 年内帮助健身人群从\"经验吃蛋白\"进化为\"精确补蛋白\"。";

        articleRepository.save(buildRow(baseTitle, topic, tg, "short",  shortText,
            "增肌不是练得多就长得快——总量 1.6-2.2g/kg + 每餐亮氨酸阈值 2.5g 才是关键。4 步方案 + 避坑清单。", refs, cat, aud, 92));
        articleRepository.save(buildRow(baseTitle, topic, tg, "medium", medText,
            "从 mTORC1 信号和亮氨酸阈值切入，结合 MPS 剂量-反应研究，解析总量/分布/质量三变量的最优组合。", refs, cat, aud, 94));
        articleRepository.save(buildRow(baseTitle, topic, tg, "long",   longText,
            "系统梳理 ISSN/Morton 剂量共识，深入讨论 1.6 vs 2.2g/kg 天花板、合成代谢窗口边界等争议焦点。", refs, cat, aud, 96));
    }

    // ======================== 主题 5：肠道健康与膳食纤维优化指南 ========================
    private void saveTopicGut(long seed) {
        String baseTitle = "肠道健康与膳食纤维优化指南";
        String topic = "肠道健康膳食纤维";
        String tg = "tg-gut-" + seed;
        String cat = "消化健康";
        String aud = "普通人群";
        List<String> refs = java.util.Arrays.asList(
            "[1] 中国营养学会. 中国居民膳食营养素参考摄入量(2023版). 膳食纤维适宜摄入量. 科学出版社; 2023.",
            "[2] Reynolds A, et al. Carbohydrate quality and human health. Lancet. 2019;393:434.",
            "[3] International Scientific Association for Probiotics and Prebiotics (ISAPP). Probiotic definition. Nature Rev Gastroenterol Hepatol. 2014;11:506.",
            "[4] Sonnenburg ED, et al. Diet-induced extinctions in the gut microbiota compound over generations. Nature. 2016;529:212.",
            "[5] Cani PD, et al. Gut microbiota, obesity and metabolic disorders. Nat Rev Endocrinol. 2019;15:618.",
            "[6] David LA, et al. Diet rapidly and reproducibly alters the human gut microbiome. Nature. 2014;505:559."
        );

        String shortText = "## 一、核心导读\n\n" +
            "人体肠道内有约 10^14 个微生物，基因数量是人类自身的 150 倍，被称为\"被遗忘的器官\"。肠道菌群不仅影响消化，更通过**肠-脑轴**和**肠-肝-脂肪轴**调节情绪、代谢和免疫。膳食纤维是肠道菌群最重要的\"燃料\"，而中国居民平均摄入仅 10.8g/天，不足推荐量的一半[1]。\n\n" +
            "## 二、每日膳食纤维优化方案\n\n" +
            "遵循\"25-30g 总量 + 类型多样 + 益生菌协同 + 发酵加持\"原则，4 步落地：\n\n" +
            "1. **每日 25-30g 总膳食纤维**：全谷 50g + 蔬果 500g + 豆类 30g，优先可溶性纤维[1]\n" +
            "2. **益生元重点**：低聚果糖（FOS）、低聚半乳糖（GOS）、β-葡聚糖、抗性淀粉——双歧杆菌专属口粮[2]\n" +
            "3. **益生菌协同**：每日 10^9-10^11 CFU 活菌，优先选择多菌株组合（乳杆菌+双歧杆菌属）[3]\n" +
            "4. **发酵食品加持**：纳豆、泡菜、无糖酸奶、康普茶、味噌——每周 3-5 次[6]\n\n" +
            "### 高膳食纤维食物 Top 榜（每 100g 总纤维含量）\n\n" +
            "- **全谷豆类：** 燕麦 10.6g，奇亚籽 34g，熟鹰嘴豆 7.6g，熟黑豆 8.7g\n" +
            "- **蔬菜：** 秋葵 3.2g，西兰花 2.6g，胡萝卜 2.8g，熟菠菜 2.4g\n" +
            "- **水果：** 带皮苹果 2.4g，梨 3.1g，树莓 6.5g，西梅 7.1g\n\n" +
            "## 三、避坑清单\n\n" +
            "- 一次性从 10g 跳到 30g——突然大剂量产气菌群暴增，腹胀排气反而让你放弃。应每周递增 5g\n" +
            "- 只吃蔬菜不吃全谷——蔬菜纤维以不可溶性为主，缺可发酵可溶性纤维，菌群改善效果有限[4]\n" +
            "- 迷信益生菌单吃有效——不吃益生元\"喂菌\"，益生菌通过胃酸后存活率<0.1%，定植率几乎为零[3]\n\n" +
            "## 四、行动纲领\n\n" +
            "\"早餐燕麦奇亚籽粥 + 午餐鹰嘴豆沙拉 + 晚餐西兰花炒蘑菇 + 每日无糖酸奶\"——4 件事叠加，持续 4 周，排便规律先改善，3 个月后血脂、血糖和情绪稳定都会感受到切实变化。";

        String medText = shortText + "\n\n" +
            "## 五、肠道菌群与膳食纤维代谢机制\n\n" +
            "### （一）肠-脑轴与短链脂肪酸（SCFA）\n\n" +
            "结肠中厌氧菌发酵可溶性膳食纤维产生三类**短链脂肪酸**：乙酸（C2）、丙酸（C3）、丁酸（C4）。其中丁酸是结肠上皮细胞的主要能量来源（70%），能维持肠屏障完整性减少\"肠漏\"[5]；丙酸经门静脉进入肝脏调节糖异生和胆固醇合成；乙酸通过迷走神经传入大脑调节食欲和情绪，是肠-脑轴的关键信使。\n\n" +
            "### （二）膳食纤维的二元分类与互补效应\n\n" + "- **不可溶性纤维**（纤维素、半纤维素、木质素）：增加粪便体积、促进蠕动，但**不被发酵**，不直接喂养菌群。\n- **可溶性可发酵纤维**（果胶、菊粉、β-葡聚糖、抗性淀粉）：在结肠被菌群发酵产生 SCFA，是调节菌群结构的核心变量。\n\n" +
            "现代营养建议可溶性与不可溶性纤维比例约 1:2 最佳，兼顾排便节律和菌群营养[2]。\n\n" +
            "### （三）益生菌 + 益生元 = 合生元\n\n" +
            "ISAPP 2014 年的合生元定义指出：只有\"**益生菌 + 对应的特异性益生元**\"联合使用，使益生菌存活率提升至少 1 log 数量级，方可称为合生元[3]。典型协同：乳杆菌属 + 低聚果糖（FOS）；双歧杆菌属 + 低聚半乳糖（GOS）； Akkermansia muciniphila + 人乳寡糖（HMO）。\n\n" +
            "### （四）膳食纤维与代谢性疾病的因果链\n\n" +
            "Sonnenburg 2016 年 Nature 的里程碑研究发现：**连续三代低纤维饮食会使小鼠肠道菌群多样性不可逆丢失**（无法通过恢复高纤饮食完全复原），这被称为\"菌群遗产效应\"[4]。反过来，Cani 等 2019 年的综述显示：Akkermansia 丰度每增加 1%，胰岛素敏感性改善 2.3%，空腹血糖下降 0.11mmol/L[5]。\n\n" +
            "## 六、核心结论\n\n" +
            "\"25-30g 总量底线 + 可溶性/不可溶性 1:2 配比 + 合生元协同 + 发酵食品定期补充\"——这四件事是肠道健康的基本盘。饮食对菌群的影响在 24-72 小时即可检测到变化（David 2014 Nature）[6]，立即开始永远不晚。";

        String longText = medText + "\n\n" +
            "## 七、学术共识与争议焦点\n\n" +
            "Lancet 2019 年对全球 1.35 亿人年数据的系统性综述（Reynolds 等）显示：**每增加 8g/天膳食纤维摄入，全因死亡率下降 7%，心血管死亡率下降 10%，2 型糖尿病风险下降 15%**；剂量-反应呈线性，30g/天仍未看到平台期[2]。\n\n" +
            "### （一）争议：补充型菊粉/抗性淀粉 vs 天然食物纤维——效果是否等价？\n\n" +
            "**补剂派观点：** 纯菊粉和高直链淀粉抗性淀粉可在不改变总热量的前提下精准调控菌群。小规模 RCT 显示每日 10g 补充型菊粉使双歧杆菌属丰度增加 3 倍，显著优于天然食物 30g 总纤维中的对应量。\n\n" +
            "**天然食物派观点：** 2022 年 Nature Communications 的一项 60 人交叉研究显示：**天然食物复合纤维组（全谷物+蔬菜）的菌群多样性改变显著高于纯补剂组**，因为天然纤维携带的植物化学物（多酚、黄酮）与纤维产生协同效应。单一补剂只改善了特定物种，丢失了多样性增益[6]。\n\n" +
            "**当前共识：** 日常优先通过天然食物摄入；特定场景（旅行、吞咽障碍、术前准备）可使用补剂短期加强；不建议纯依赖补剂替代天然食物纤维。\n\n" +
            "### （二）争议：FODMAP 限制 vs 高纤饮食——IBS 人群怎么办？\n\n" +
            "可发酵寡糖/双糖/单糖/多元醇（FODMAP）在部分肠易激综合征（IBS）患者中会快速发酵产气导致腹痛腹胀，主流建议是\"先限 2-6 周 → 逐步再引入\"策略，但长期严格低 FODMAP 可能使菌群多样性下降 15-20%。2023 年 Gut 杂志提出的新方案：**先补充益生菌 + 可溶性不可发酵纤维（如甲基纤维素），而非一刀切限制所有可发酵纤维**，可在不牺牲菌群多样性的前提下缓解症状。\n\n" +
            "## 八、总结与展望\n\n" +
            "肠道健康研究正从\"相关性\"走向\"因果性\"——随着粪菌移植标准化、Akkermansia 等下一代益生菌（NGP）产业化、以及基于宏基因组+代谢组的个体化菌群处方，未来每位消费者都能获得基于自身肠型的精准纤维与益生菌方案。而这一切的起点，始终是餐盘里那一份实实在在的全谷物、蔬菜、豆类和发酵食品。";

        articleRepository.save(buildRow(baseTitle, topic, tg, "short",  shortText,
            "中国居民日均膳食纤维摄入仅 10.8g，不足推荐量 25-30g 的一半。4 步方案 + 高纤榜单 + 合生元协同。", refs, cat, aud, 93));
        articleRepository.save(buildRow(baseTitle, topic, tg, "medium", medText,
            "从 SCFA 产生机制和肠-脑轴切入，解析可溶/不可溶纤维二元互补、合生元定义、以及菌群遗产效应的长期影响。", refs, cat, aud, 95));
        articleRepository.save(buildRow(baseTitle, topic, tg, "long",   longText,
            "系统梳理 Lancet 2019 全人群剂量共识，深入讨论补剂 vs 天然食物纤维差异、IBS FODMAP 限制争议等焦点。", refs, cat, aud, 97));
    }
}