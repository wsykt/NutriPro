package com.health.util;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.*;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * BGE 向量知识库检索工具类。
 *
 * 封装对 Python AI 服务 /api/v1/retrieve 端点的调用，
 * 统一为 AI 饮食咨询模块和科普文章生成模块提供 RAG 知识素材。
 *
 * 使用场景：
 * 1. AI 饮食咨询：用户询问食物营养/慢病膳食知识时，触发检索注入参考片段
 * 2. 科普文章生成：强制触发检索，作为母稿创作的事实依据，降低大模型幻觉
 */
public class RagVectorSearchUtil {

    private static final int CONNECT_TIMEOUT = 5000;
    private static final int READ_TIMEOUT = 15000;
    /** 相似度阈值：仅 ≥ 此值的片段才注入提示词 */
    private static final double SIMILARITY_THRESHOLD = 0.6;

    private String aiBaseUrl = "http://localhost:8002/api/v1";
    private RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    public RagVectorSearchUtil() {
        this.objectMapper = new ObjectMapper();
    }

    /**
     * 设置 RestTemplate（由调用方传入，工具类不走 Bean 注入）。
     */
    public void setRestTemplate(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    /**
     * 设置 AI 服务 API 基础 URL。
     */
    public void setAiBaseUrl(String aiBaseUrl) {
        this.aiBaseUrl = aiBaseUrl;
    }

    /**
     * 执行向量检索，返回格式化的知识素材文本。
     * v2.2 改进：相似度阈值过滤（≥0.6）+ 参考素材编号 [1][2]...
     *
     * @param query        检索查询（用户问题或文章主题）
     * @param topK         返回结果数量
     * @param targetCrowd  目标人群（可选，用于过滤）
     * @return 格式化的知识素材文本；无结果或异常时返回空字符串
     */
    public String search(String query, int topK, String targetCrowd) {
        if (query == null || query.trim().isEmpty()) {
            return "";
        }

        try {
            Map<String, Object> requestBody = new LinkedHashMap<>();
            requestBody.put("query", query);
            requestBody.put("top_k", topK);
            if (targetCrowd != null && !targetCrowd.isEmpty()) {
                requestBody.put("target_crowd", targetCrowd);
            }

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            ResponseEntity<String> response = restTemplate.postForEntity(
                    aiBaseUrl + "/retrieve", entity, String.class);

            if (response.getBody() == null) {
                return "";
            }

            Map<String, Object> responseMap = objectMapper.readValue(response.getBody(), Map.class);
            List<Map<String, Object>> results = (List<Map<String, Object>>) responseMap.get("results");

            if (results == null || results.isEmpty()) {
                return "";
            }

            // v2.2：相似度阈值过滤
            List<Map<String, Object>> filtered = new java.util.ArrayList<>();
            for (Map<String, Object> r : results) {
                Object simObj = r.get("similarity");
                double sim = 0;
                if (simObj instanceof Number) {
                    sim = ((Number) simObj).doubleValue();
                }
                if (sim >= SIMILARITY_THRESHOLD) {
                    filtered.add(r);
                }
            }

            if (filtered.isEmpty()) {
                return "";
            }

            return formatResultsWithNumbering(filtered);
        } catch (Exception e) {
            // 检索失败不影响主流程，返回空字符串
            return "";
        }
    }

    /**
     * 快捷方法：默认 topK=3，不限定人群
     */
    public String search(String query) {
        return search(query, 3, null);
    }

    /**
     * 将检索结果格式化为带编号的知识素材文本（v3.1：[1][2]编号 + 来源类型标注 + 来源渠道，支持完整溯源）。
     *
     * 来源类型：
     * - [向量知识库]：本地BGE向量知识库检索命中
     * - [Agent联网搜索]：Agent通过PubMed等渠道联网搜集的资料
     *
     * 来源渠道（v3.1新增）：
     * - PubMed：PubMed科研文献
     * - 官方指南：中国居民膳食指南、WHO报告等
     * - 权威报告：权威机构发布的报告
     */
    private String formatResultsWithNumbering(List<Map<String, Object>> results) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < results.size(); i++) {
            Map<String, Object> r = results.get(i);
            sb.append("[").append(i + 1).append("] ");

            // 来源类型（v3.0新增）
            String sourceType = "[向量知识库]";
            // 来源渠道（v3.1新增）
            String sourceChannel = "";
            Object metaObj = r.get("metadata");
            if (metaObj instanceof Map) {
                Map<String, Object> meta = (Map<String, Object>) metaObj;
                // 检查是否为Agent联网搜索的来源
                Object catType = meta.get("category");
                if (catType != null) {
                    String cat = catType.toString();
                    if ("web_acquired".equals(cat) || "research_paper".equals(cat)) {
                        sourceType = "[Agent联网搜索]";
                    }
                }
                // 检查显式标记的source_type
                Object st = meta.get("source_type");
                if (st != null && "agent_search".equals(st.toString())) {
                    sourceType = "[Agent联网搜索]";
                }
                // 来源渠道（v3.1新增）
                Object channelObj = meta.get("source_channel");
                if (channelObj != null) {
                    sourceChannel = channelObj.toString();
                }
                // 检查是否为官方指南
                Object isGuide = meta.get("is_official_guide");
                if (isGuide != null && "true".equals(isGuide.toString())) {
                    sourceChannel = "官方指南";
                }
            }
            
            // 输出来源类型和渠道（v3.1更新）
            sb.append(sourceType);
            if (!sourceChannel.isEmpty()) {
                sb.append("（来源渠道：").append(sourceChannel).append("）");
            }
            sb.append(" ");

            // 来源
            String source = "";
            if (metaObj instanceof Map) {
                Object src = ((Map<String, Object>) metaObj).get("source");
                if (src != null) source = src.toString();
            }
            if (source.isEmpty() && r.get("source") != null) {
                source = r.get("source").toString();
            }
            if (!source.isEmpty()) {
                sb.append("（来源：").append(source).append("）");
            }
            sb.append("\n");

            // 内容
            if (r.get("content") != null) {
                String content = r.get("content").toString();
                if (content.length() > 800) {
                    content = content.substring(0, 800) + "...";
                }
                sb.append(content).append("\n");
            }

            // 相似度
            Object simObj = r.get("similarity");
            if (simObj instanceof Number) {
                double sim = ((Number) simObj).doubleValue();
                sb.append("（相似度：").append(Math.round(sim * 100)).append("%）\n");
            }
            sb.append("\n");
        }
        return sb.toString().trim();
    }

    // ======================== RAG 素材热度统计 ========================

    /**
     * 记录 RAG 检索使用情况（不自动入库，仅统计热度，辅助管理员识别知识缺口）。
     *
     * @param query    检索查询
     * @param scenario 使用场景（article_generation / ai_consultation）
     * @param crowd    目标人群
     */
    public void logRagUsage(String query, String scenario, String crowd) {
        try {
            Map<String, Object> requestBody = new LinkedHashMap<>();
            requestBody.put("query", query != null ? query : "");
            requestBody.put("scenario", scenario != null ? scenario : "");
            requestBody.put("target_crowd", crowd != null ? crowd : "");

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            restTemplate.postForEntity(aiBaseUrl + "/knowledge/log-usage", entity, String.class);
        } catch (Exception ignored) {
            // 热度统计失败不影响主流程
        }
    }

    /**
     * 获取 RAG 素材热度统计报表。
     */
    public Map<String, Object> getHotStats() {
        try {
            ResponseEntity<String> response = restTemplate.getForEntity(
                    aiBaseUrl + "/knowledge/hot-stat", String.class);
            if (response.getBody() == null) {
                return Collections.emptyMap();
            }
            return objectMapper.readValue(response.getBody(), Map.class);
        } catch (Exception e) {
            Map<String, Object> err = new LinkedHashMap<>();
            err.put("error", "获取热度统计失败: " + e.getMessage());
            return err;
        }
    }

    // ======================== 知识库自学习：联网获取权威资料 ========================

    /**
     * 知识库自学习：从互联网获取权威资料并入库。
     *
     * 两种模式：
     * 1. 主题搜索：提供 topic，自动搜索权威来源（科普文章、科研论文、官方数据）→ 抓取 → 入库
     * 2. URL 抓取：提供具体 URL 列表，直接抓取内容 → 入库
     *
     * @param topic       搜索主题（模式1）
     * @param urls        URL 列表（模式2，可为 null）
     * @param maxResults  最大获取数量
     * @param targetCrowd 目标人群
     * @return 获取结果 Map
     */
    public Map<String, Object> acquireKnowledge(String topic, List<String> urls,
                                                 int maxResults, String targetCrowd) {
        Map<String, Object> result = new LinkedHashMap<>();

        if ((topic == null || topic.trim().isEmpty()) &&
            (urls == null || urls.isEmpty())) {
            result.put("success", false);
            result.put("message", "请提供 topic 或 urls");
            return result;
        }

        try {
            // 设置更长的超时（联网搜索+抓取需要更多时间）
            SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
            factory.setConnectTimeout(CONNECT_TIMEOUT);
            factory.setReadTimeout(60000); // 60秒
            RestTemplate longRestTemplate = new RestTemplate(factory);

            Map<String, Object> requestBody = new LinkedHashMap<>();
            if (topic != null && !topic.trim().isEmpty()) {
                requestBody.put("topic", topic);
            }
            if (urls != null && !urls.isEmpty()) {
                requestBody.put("urls", urls);
            }
            requestBody.put("max_results", maxResults);
            if (targetCrowd != null) {
                requestBody.put("target_crowd", targetCrowd);
            }

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            ResponseEntity<String> response = longRestTemplate.postForEntity(
                    aiBaseUrl + "/knowledge/acquire", entity, String.class);

            if (response.getBody() == null) {
                result.put("success", false);
                result.put("message", "AI 服务返回空响应");
                return result;
            }

            return objectMapper.readValue(response.getBody(), Map.class);
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", "知识获取失败: " + e.getMessage());
            return result;
        }
    }

    /**
     * 快捷方法：按主题搜索并入库。
     */
    public Map<String, Object> acquireKnowledge(String topic, String targetCrowd) {
        return acquireKnowledge(topic, null, 3, targetCrowd);
    }

    // ======================== 方案C：混合架构 Agent 调用 ========================

    /**
     * 调用资料搜集Agent：基于主题+已有素材S1，联网搜索补充缺失的权威资料S2。
     *
     * @param topic             主题
     * @param existingMaterials 已有素材S1文本摘要
     * @param maxResults        最大补充数量
     * @param targetCrowd       目标人群
     * @return Agent 返回结果，包含 new_materials 列表
     */
    public Map<String, Object> searchMaterialsAgent(String topic, String existingMaterials,
                                                     int maxResults, String targetCrowd) {
        try {
            SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
            factory.setConnectTimeout(CONNECT_TIMEOUT);
            factory.setReadTimeout(120000); // 联网搜索需要更长超时
            RestTemplate agentRestTemplate = new RestTemplate(factory);

            Map<String, Object> requestBody = new LinkedHashMap<>();
            requestBody.put("topic", topic);
            requestBody.put("existing_materials", existingMaterials != null ? existingMaterials : "");
            requestBody.put("max_results", maxResults);
            requestBody.put("target_crowd", targetCrowd != null ? targetCrowd : "");

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            ResponseEntity<String> response = agentRestTemplate.postForEntity(
                    aiBaseUrl + "/agent/search-materials", entity, String.class);

            if (response.getBody() == null) {
                Map<String, Object> err = new LinkedHashMap<>();
                err.put("success", false);
                err.put("message", "Agent 返回空响应");
                return err;
            }

            return objectMapper.readValue(response.getBody(), Map.class);
        } catch (Exception e) {
            Map<String, Object> err = new LinkedHashMap<>();
            err.put("success", false);
            err.put("message", "资料搜集Agent调用失败: " + e.getMessage());
            return err;
        }
    }

    /**
     * 调用事实校验Agent：核查母稿中所有引用是否有素材支撑。
     *
     * @param draft          科普母稿全文
     * @param sourceMaterials 素材集合S全文
     * @return 校验结果，包含 passed、score、defects
     */
    public Map<String, Object> factCheckAgent(String draft, String sourceMaterials) {
        try {
            Map<String, Object> requestBody = new LinkedHashMap<>();
            requestBody.put("draft", draft);
            requestBody.put("source_materials", sourceMaterials != null ? sourceMaterials : "");

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            ResponseEntity<String> response = restTemplate.postForEntity(
                    aiBaseUrl + "/agent/fact-check", entity, String.class);

            if (response.getBody() == null) {
                Map<String, Object> err = new LinkedHashMap<>();
                err.put("success", false);
                err.put("passed", false);
                err.put("summary", "校验Agent返回空响应");
                return err;
            }

            return objectMapper.readValue(response.getBody(), Map.class);
        } catch (Exception e) {
            Map<String, Object> err = new LinkedHashMap<>();
            err.put("success", false);
            err.put("passed", false);
            err.put("summary", "事实校验Agent调用失败: " + e.getMessage());
            return err;
        }
    }

    /**
     * 判断用户问题是否需要触发向量检索。
     * 仅当问题涉及食物营养知识、慢病膳食、食材功效等知识性问题时触发；
     * 日常饮食记录分析、膳食计划优化不强制检索。
     */
    public static boolean shouldRetrieveForConsultation(String question) {
        if (question == null || question.trim().isEmpty()) {
            return false;
        }
        String q = question.toLowerCase();
        // 知识性咨询关键词
        String[] knowledgeKeywords = {
            "营养", "功效", "作用", "好处", "维生素", "矿物质", "蛋白质",
            "膳食纤维", "gi值", "升糖", "热量", "卡路里",
            "糖尿病", "高血压", "高血脂", "痛风", "肾病",
            "孕妇", "老年人", "青少年", "健身",
            "什么食物", "哪些食物", "能不能吃", "可以吃吗",
            "区别", "对比", "哪个好", "怎么选"
        };
        for (String kw : knowledgeKeywords) {
            if (q.contains(kw)) {
                return true;
            }
        }
        return false;
    }

    // ======================== 知识库自学习：文档摄入 ========================

    /**
     * 向向量知识库写入新文档（知识库自学习）。
     *
     * 调用 Python AI 服务 /api/v1/knowledge/ingest 端点，
     * 将文档分块后生成 BGE 向量并写入 Chroma 向量库。
     *
     * 使用场景：
     * 1. 管理员手动提交官方文档、科研文章
     * 2. 系统自动将高质量科普文章回写到知识库（ArticleService 自动调用）
     *
     * @param content      文档全文文本
     * @param source       来源标识（如"中国居民膳食指南2022"、"科普文章：补钙"）
     * @param category     分类（dietary_guideline/nutrition_standard/science_article 等）
     * @param targetCrowd  适用人群（留空则通用）
     * @return 摄入结果 Map，包含 success、chunks_added 等
     */
    public Map<String, Object> ingestDocument(String content, String source,
                                               String category, String targetCrowd) {
        Map<String, Object> result = new LinkedHashMap<>();

        if (content == null || content.trim().isEmpty()) {
            result.put("success", false);
            result.put("message", "content 不能为空");
            return result;
        }

        try {
            Map<String, Object> requestBody = new LinkedHashMap<>();
            requestBody.put("content", content);
            requestBody.put("source", source != null ? source : "未知来源");
            requestBody.put("category", category != null ? category : "science_article");
            requestBody.put("target_crowd", targetCrowd != null ? targetCrowd : "");
            requestBody.put("chunk_size", 600);
            requestBody.put("overlap", 100);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(requestBody), headers);

            ResponseEntity<String> response = restTemplate.postForEntity(
                    aiBaseUrl + "/knowledge/ingest", entity, String.class);

            if (response.getBody() == null) {
                result.put("success", false);
                result.put("message", "AI 服务返回空响应");
                return result;
            }

            Map<String, Object> responseMap = objectMapper.readValue(response.getBody(), Map.class);
            return responseMap;
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", "知识库写入失败: " + e.getMessage());
            return result;
        }
    }

    /**
     * 查询知识库中的文档列表。
     */
    public Map<String, Object> listDocuments(int limit) {
        try {
            ResponseEntity<String> response = restTemplate.getForEntity(
                    aiBaseUrl + "/knowledge/list?limit=" + limit, String.class);

            if (response.getBody() == null) {
                return Collections.emptyMap();
            }

            return objectMapper.readValue(response.getBody(), Map.class);
        } catch (Exception e) {
            Map<String, Object> err = new LinkedHashMap<>();
            err.put("error", "查询失败: " + e.getMessage());
            return err;
        }
    }
}
