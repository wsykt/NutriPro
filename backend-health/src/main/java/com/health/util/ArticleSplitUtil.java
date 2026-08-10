package com.health.util;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 科普文章母稿拆分工具类。
 *
 * AI 一次调用返回带 【#标记名#】 的母稿文本，本类负责：
 * 1. normalizeMarkers  清洗标记格式（全角→半角、标记独占一行）
 * 2. parseBlocks        按标记切成 {标记名: 内容} 字典
 * 3. splitMotherDraft   按区块保留规则拼装出 速读卡/深度文/综述文 三版
 * 4. cleanShortContent  速读版清洗（去大表格、去机制段落）
 * 5. parseMeta/parseRefs 解析 META 元信息与 REF_LIST 参考文献
 * 6. validate           五道自动化校验（篇幅/参考文献/数值/敏感词/查重）
 */
public class ArticleSplitUtil {

    // ======================== 内部结果类 ========================

    /** 拆分结果 */
    public static class SplitResult {
        public String shortText;
        public String mediumText;
        public String longText;
        public Map<String, String> meta;
        public List<String> refs;
        public Map<String, String> summaries;   // short / medium / long
        public Map<String, String> conclusions; // short / medium / long

        public SplitResult() {
            meta = new LinkedHashMap<>();
            refs = new ArrayList<>();
            summaries = new LinkedHashMap<>();
            conclusions = new LinkedHashMap<>();
        }
    }

    /** 校验结果 */
    public static class ValidationResult {
        public boolean passed;
        public int score;
        public List<String> errors;

        public ValidationResult(boolean passed, int score, List<String> errors) {
            this.passed = passed;
            this.score = score;
            this.errors = errors;
        }
    }

    // ======================== 1. 标记清洗 ========================

    /**
     * 归一化标记格式：
     * - 全角空格→半角
     * - 统一标记符号为【#TAG#】（兼容全角【［[]】］）
     * - 标记内去多余空格
     * - 统一换行
     * - 标记独占一行（标记后若紧跟内容则插入换行）
     */
    public static String normalizeMarkers(String text) {
        if (text == null) return "";
        return text
                .replace("\u3000", " ")
                .replaceAll("[【［\\[]\\s*#\\s*([A-Z_]+)\\s*#\\s*[】］\\]]", "【#$1#】")
                .replaceAll("([【】])\\s+", "$1")
                .replace("\r\n", "\n")
                .replaceAll("【#([A-Z_]+)#】\\s*([^\\n])", "【#$1#】\n$2");
    }

    // ======================== 2. 区块解析 ========================

    /**
     * 按 【#TAG#】 标记把母稿切成 {标记名: 内容} 字典。
     * BEGIN/END 成对标记取 BEGIN 到对应 END 之间的内容（去 END 标记行）。
     */
    public static Map<String, String> parseBlocks(String rawText) {
        Map<String, String> blocks = new LinkedHashMap<>();
        if (rawText == null) return blocks;

        Pattern re = Pattern.compile("【#([A-Z_]+)#】\\s*([\\s\\S]*?)(?=【#[A-Z_]+#】|$)");
        Matcher m = re.matcher(rawText);
        while (m.find()) {
            String tag = m.group(1).trim();
            String content = m.group(2).trim();
            // 对于 BEGIN/END 成对标记，只保留 BEGIN，去掉 END 标记行
            if (tag.endsWith("_END")) {
                continue; // END 标记不单独存储
            }
            if (tag.endsWith("_BEGIN")) {
                // 去掉内容末尾可能残留的 END 标记行
                String baseTag = tag.substring(0, tag.length() - "_BEGIN".length());
                content = content.replaceAll("【#" + baseTag + "_END#】[\\s\\S]*$", "").trim();
                blocks.put(baseTag, content);
            } else {
                blocks.put(tag, content);
            }
        }
        return blocks;
    }

    // ======================== 3. 三版拼装 ========================

    /**
     * 母稿拆分为三版：
     * - 速读卡 = 引言 + 共识(清洗后) + 速读结论
     * - 深度文 = 引言 + 共识 + 深度拓展 + 深度结论
     * - 综述文 = 引言 + 共识 + 深度拓展 + 学术争议 + 综述结论
     */
    public static SplitResult splitMotherDraft(String rawText, String persona) {
        String normalized = normalizeMarkers(rawText);
        Map<String, String> blocks = parseBlocks(normalized);

        SplitResult result = new SplitResult();

        // 没有共识或引言则拆分失败
        String common = cleanTemplateLines(blocks.getOrDefault("COMMON", ""));
        String intro = cleanTemplateLines(blocks.getOrDefault("ALL_INTRO", ""));
        if (common.isEmpty() && intro.isEmpty()) {
            return null;
        }

        String deepPlus = cleanTemplateLines(blocks.getOrDefault("DEEP_PLUS", ""));
        String debate = cleanTemplateLines(blocks.getOrDefault("DEBATE_ZONE", ""));
        String concludeFast = cleanTemplateLines(blocks.getOrDefault("CONCLUDE_FAST", ""));
        String concludeDeep = cleanTemplateLines(blocks.getOrDefault("CONCLUDE_DEEP", ""));
        String concludeAll = cleanTemplateLines(blocks.getOrDefault("CONCLUDE_ALL", ""));

        // 三版拼装
        String shortRaw = joinNonEmpty("\n\n", intro, common, concludeFast);
        String medium = joinNonEmpty("\n\n", intro, common, deepPlus, concludeDeep);
        String longText = joinNonEmpty("\n\n", intro, common, deepPlus, debate, concludeAll);

        // 速读版清洗
        result.shortText = cleanShortContent(shortRaw);
        result.mediumText = medium;
        result.longText = longText;

        // 元信息与参考文献
        result.meta = parseMeta(blocks.getOrDefault("META", ""), persona);
        result.refs = parseRefs(blocks.getOrDefault("REF_LIST", ""));

        // 摘要与结论
        result.summaries.put("short", blocks.getOrDefault("SUMMARY_FAST", ""));
        result.summaries.put("medium", blocks.getOrDefault("SUMMARY_DEEP", ""));
        result.summaries.put("long", blocks.getOrDefault("SUMMARY_ALL", ""));

        result.conclusions.put("short", concludeFast);
        result.conclusions.put("medium", concludeDeep);
        result.conclusions.put("long", concludeAll);

        return result;
    }

    // ======================== 3.5 模板占位行清洗 ========================

    /**
     * 清洗模型误写入正文的模板占位说明行（与前端 articleRendering.ts 兜底逻辑对齐）。
     * 模型不严格遵守提示词【总则】，会把 build_mother_format 中的占位说明行原样写入正文，例如：
     *   "通用引言（2~3句话）：点明健身人士人群核心痛点+1条流行病学数据"
     *   "共识基础内容（400~900字，参考约600字）：底层原理、每日营养素需求量、食物来源清单、通用行动清单"
     *   "一级标题：一、增肌期蛋白质摄入的重要性；二级标题：（一）肌肉合成与分解的平衡"
     *   "深度拓展（600~1350字，参考约900字）：特殊人群、细分场景深度拓展"
     *   "深度文结论：内容总结+核心膳食建议"
     * 处理规则：
     *   1) 纯占位说明行（通用引言/共识基础内容/摘要类/板块标题格式说明）→ 整行删除
     *   2) 板块说明行（结论/深度拓展/学术争议/参考文献）→ 规范化为 "## 板块名" 独立标题
     *   3) "一级标题：一、xxx；二级标题：（一）yyy" → 提取真实一级标题恢复 "## 一、xxx"
     */
    public static String cleanTemplateLines(String text) {
        if (text == null) return "";
        String s = text;
        // 注意：行级正则一律用 [ \t] 与 [^\n] 限定，避免 \s* 跨行吞掉正文
        // 1) 纯占位说明行删除（须带冒号）
        s = s.replaceAll("(?m)^[ \\t]*通用引言[ \\t]*(?:（[^\\n）]*）)?[ \\t]*[:：][^\\n]*$", "");
        s = s.replaceAll("(?m)^[ \\t]*共识基础内容[ \\t]*(?:（[^\\n）]*）)?[ \\t]*[:：][^\\n]*$", "");
        s = s.replaceAll("(?m)^[ \\t]*板块标题单独一行[^\\n]*$", "");
        s = s.replaceAll("(?m)^[ \\t]*(?:速读卡摘要|深度文摘要|综述摘要)[ \\t]*(?:（[^\\n）]*）)?[ \\t]*[:：][^\\n]*$", "");
        // 2) 板块说明行 → ## 标题
        s = s.replaceAll("(?m)^[ \\t]*(?:速读卡结论|深度文结论|综述结论|核心结论|研究结论|总结)[ \\t]*(?:（[^\\n）]*）)?[ \\t]*[:：][^\\n]*$", "\n## 结论\n");
        s = s.replaceAll("(?m)^[ \\t]*细分场景深度拓展[ \\t]*(?:（[^\\n）]*）)?[ \\t]*[:：][^\\n]*$", "\n## 细分场景深度拓展\n");
        s = s.replaceAll("(?m)^[ \\t]*深度拓展[ \\t]*(?:（[^\\n）]*）)?[ \\t]*[:：][^\\n]*$", "\n## 深度拓展\n");
        s = s.replaceAll("(?m)^[ \\t]*学术争议[ \\t]*(?:（[^\\n）]*）)?[ \\t]*[:：][^\\n]*$", "\n## 学术争议\n");
        s = s.replaceAll("(?m)^[ \\t]*参考文献[ \\t]*[0-9]*~?[0-9]*条?[ \\t]*[:：][^\\n]*$", "\n## 参考文献\n");
        // 3) "一级标题：一、xxx；二级标题：…" → 提取真实一级标题；纯编号序列（"一级标题：一、二、三"）→ 整行删除
        Pattern h1Pat = Pattern.compile("(?m)^[ \\t]*一级标题[ \\t]*[:：][ \\t]*([一二三四五六七八九十百]+、[^\\n；;]*?)[ \\t]*(?:[；;][^\\n；;]*)?$");
        Matcher h1M = h1Pat.matcher(s);
        StringBuffer h1Sb = new StringBuffer();
        while (h1M.find()) {
            String cand = h1M.group(1).trim();
            String rest = cand.replaceFirst("^[一二三四五六七八九十百]+、", "").trim();
            if (rest.isEmpty() || rest.matches("^[一二三四五六七八九十百]+、.*")) {
                h1M.appendReplacement(h1Sb, "");
            } else {
                h1M.appendReplacement(h1Sb, Matcher.quoteReplacement("\n## " + cand + "\n"));
            }
        }
        h1M.appendTail(h1Sb);
        s = h1Sb.toString();
        // 3.5) 兜底删除：多分号「一级标题：一、A；二、B；三、C」说明行（正文已含真实标题）→ 整行删除
        s = s.replaceAll("(?m)^[ \\t]*一级标题[ \\t]*[:：][ \\t]*[^\\n]*$", "");
        // 4) 裸标题兜底删除
        s = s.replaceAll("(?m)^[ \\t]*通用引言[ \\t]*$", "");
        s = s.replaceAll("(?m)^[ \\t]*共识基础内容[ \\t]*$", "");
        // 清理连续 3+ 换行
        s = s.replaceAll("\\n{3,}", "\n\n").trim();
        return s;
    }

    // ======================== 4. 速读版清洗 ========================

    /**
     * 速读卡清洗：
     * 1. 去掉 8 行以上的大表格（用量参考表等）
     * 2. 去掉不含标题但含"机制/通路/受体/酶活性"的深度段落
     */
    public static String cleanShortContent(String content) {
        if (content == null) return "";
        String text = content;
        // 规则1：去掉大表格（连续 8 行以上的 | 开头行）
        text = text.replaceAll("(\\|[^\\n]+\\n){8,}", "");
        // 规则2：去掉含机制关键词的深度段落（行首50字内含关键词且整行超50字）
        text = text.replaceAll("^[^#\\n]{0,50}(?:生理机制|分子机制|信号通路|受体|酶活性)[^\\n]{50,}\\n?", "");
        return text.trim();
    }

    // ======================== 5. META / REF 解析 ========================

    /**
     * 解析 META 区块：按行拆 "key：value"。
     */
    public static Map<String, String> parseMeta(String metaText, String persona) {
        Map<String, String> meta = new LinkedHashMap<>();
        if (persona != null) meta.put("persona", persona);
        if (metaText == null) return meta;

        for (String line : metaText.split("\n")) {
            int idx = line.indexOf("：");
            if (idx <= 0) idx = line.indexOf(":");
            if (idx > 0) {
                meta.put(line.substring(0, idx).trim(), line.substring(idx + 1).trim());
            }
        }
        return meta;
    }

    /**
     * 解析 REF_LIST 区块：提取 [序号] 开头的行。
     */
    public static List<String> parseRefs(String refText) {
        List<String> refs = new ArrayList<>();
        if (refText == null) return refs;
        for (String line : refText.split("\n")) {
            String trimmed = line.trim();
            if (trimmed.matches("\\[\\d+\\].*")) {
                refs.add(trimmed);
            }
        }
        return refs;
    }

    // ======================== 6. 五道校验 ========================

    /**
     * 五道自动化校验：
     * ① 篇幅区间  ② 参考文献  ③ 营养数值  ④ 敏感话术  ⑤ (查重预留)
     */
    public static ValidationResult validate(SplitResult split) {
        List<String> errors = new ArrayList<>();
        int score = 100;

        // ① 篇幅区间（中文字符数）
        int shortLen = countChinese(split.shortText);
        int mediumLen = countChinese(split.mediumText);
        int longLen = countChinese(split.longText);
        // 字数上限与母稿模板对齐：
        // 速读=引言+COMMON(400~900)+速读结论；深度文=+DEEP(600~1350)+深度结论；综述文=+DEBATE(≤800)+综述结论
        if (shortLen < 50 || shortLen > 900) { errors.add("速读字数" + shortLen + "异常"); score -= 15; }
        if (mediumLen < 300 || mediumLen > 2500) { errors.add("深度文字数" + mediumLen + "异常"); score -= 15; }
        if (longLen < 500 || longLen > 4000) { errors.add("综述文字数" + longLen + "异常"); score -= 15; }

        // ② 参考文献
        if (split.refs.size() < 3) { errors.add("参考文献不足3条"); score -= 15; }

        // ③ 营养数值异常（超出合理剂量范围的数值+单位）
        // 注：孕期钙推荐量 1200mg、每日能量 2000kcal 等为正常值，按单位设置合理阈值避免误伤
        String allText = split.shortText + split.mediumText + split.longText;
        Pattern suspiciousPattern = Pattern.compile("(\\d{3,})\\s*(mg|毫克|g|克|kcal|IU|微克)");
        Matcher sm = suspiciousPattern.matcher(allText);
        List<String> suspicious = new ArrayList<>();
        while (sm.find() && suspicious.size() < 3) {
            double num = Double.parseDouble(sm.group(1));
            String unit = sm.group(2);
            boolean abnormal;
            switch (unit) {
                case "mg":
                case "毫克": abnormal = num > 4000; break;   // 钙/钾等推荐量可达1200~2000mg
                case "g":
                case "克":   abnormal = num >= 1000; break;  // 食物重量/蛋白质以百克计
                case "kcal": abnormal = num > 99999; break;  // 每日能量2000kcal正常
                case "IU":   abnormal = num > 200000; break; // 维D大剂量才达20万IU
                case "微克": abnormal = num > 5000; break;   // 叶酸/维D μg 正常≤1000
                default:     abnormal = false;
            }
            if (abnormal) suspicious.add(sm.group());
        }
        if (!suspicious.isEmpty()) { errors.add("异常数值：" + String.join(", ", suspicious)); score -= 10; }

        // ④ 敏感医疗话术
        String[] risky = {"治愈", "根治", "包治", "特效药", "偏方", "秘方", "绝对安全"};
        List<String> found = new ArrayList<>();
        for (String r : risky) {
            if (allText.contains(r)) found.add(r);
        }
        if (!found.isEmpty()) { errors.add("敏感话术：" + String.join(", ", found)); score -= 25; }

        // ⑤ 相似度查重（预留，需向量检索）
        // TODO: 接入向量检索比对已有文章

        score = Math.max(0, score);
        return new ValidationResult(errors.isEmpty() && score >= 60, score, errors);
    }

    // ======================== 工具方法 ========================

    /** 统计中文字符数 */
    public static int countChinese(String text) {
        if (text == null) return 0;
        int count = 0;
        for (char c : text.toCharArray()) {
            if (c >= '\u4e00' && c <= '\u9fa5') count++;
        }
        return count;
    }

    /** 拼接非空字符串 */
    private static String joinNonEmpty(String delimiter, String... parts) {
        StringBuilder sb = new StringBuilder();
        for (String p : parts) {
            if (p != null && !p.trim().isEmpty()) {
                if (sb.length() > 0) sb.append(delimiter);
                sb.append(p);
            }
        }
        return sb.toString();
    }
}
