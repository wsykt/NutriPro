package com.health.controller;

import com.fasterxml.jackson.databind.ObjectMapper;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * 管理员流程演示页：AI 生成流水线"每一步发生了什么"的实时步骤事件引擎。
 *
 * <p>设计目标（演示优先，轻量）：</p>
 * <ul>
 *   <li>1) 每次发起"模拟 AI 执行"都生成一个 traceId，对应一串有顺序的 {@link Step}。</li>
 *   <li>2) 步骤是"异步 + 有间隔"地追加到内存队列（不依赖真实大模型/DB IO），
 *          前端可以每 300ms 轮询拿到"刚完成的"步骤 → 做出"后端真的在跑"的时间线效果。</li>
 *   <li>3) 最后 1 步 {@link Step#last} = true 时，前端停止轮询并拿到 snapshotId，
 *          立刻跳转预览。该步骤真正调用 AiPreviewAdminController.saveSnapshot 落库。</li>
 *   <li>4) 每个 Step 都记录 input/output/耗时/时间戳，前端按时间线卡片展示，
 *          并且点击卡片可展开"放入了什么数据、产出了什么"的详情 JSON。</li>
 * </ul>
 *
 * <p>7 个 funcType 各自有独立的步骤编排（6–8 步不等），演示不同 AI 子流程。</p>
 *
 * <p>⚠️ 为演示用内存结构（ConcurrentHashMap + CopyOnWriteArrayList），重启即丢；
 *    每个 traceId 保留 30 分钟，后台有简单 TTL 清理（AiPipelineController 启动 10 分钟触发一次）。</p>
 */
public class AiPipelineEngine {

    public static class Step {
        public int index;                 // 1-based
        public String title;              // 步骤名称（显示在时间线上，例如"1. 构建用户画像上下文"）
        public String subtitle;           // 1 行说明
        public String status;             // pending / running / done / error
        public String startedAt;          // ISO
        public String finishedAt;         // ISO
        public long durationMs;           // 实际执行耗时 ms
        public Object input;              // 入参（Map/POJO → JSON 给前端看）
        public Object output;             // 出参
        public String note;               // 额外说明（如"命中知识库 X 条"）
        public boolean last;              // 最后一步 → 里面带 snapshotId
        public boolean autoDone;          // 由 AI 服务返回的真实 trace 断点展开的步骤（已执行完毕，不再走位置映射）
        public Map<String, Object> extra; // 其它（比如 token 估算、prompt 片段）
    }

    public static class Trace {
        public String traceId;
        public String funcType;
        public String sessionId;
        public String mode;
        public Integer userId;
        public String createdAt;
        public String finalSnapshotId;
        public boolean done;
        public String error;
        public List<Step> steps;          // 步骤按 index 顺序
    }

    // -------- 存储 --------
    static final Map<String, Trace> TRACES = new ConcurrentHashMap<>();
    static final Map<String, Long> TRACE_EXPIRE_AT = new ConcurrentHashMap<>();
    static final ObjectMapper OM = new ObjectMapper();
    static final DateTimeFormatter FMT = DateTimeFormatter.ISO_LOCAL_DATE_TIME;

    private static final long TRACE_TTL_MS = 30L * 60L * 1000L;

    static void touch(String traceId) {
        TRACE_EXPIRE_AT.put(traceId, System.currentTimeMillis() + TRACE_TTL_MS);
    }

    static void cleanExpired() {
        long now = System.currentTimeMillis();
        List<String> toRemove = new ArrayList<>();
        for (Map.Entry<String, Long> e : TRACE_EXPIRE_AT.entrySet()) {
            if (e.getValue() < now) toRemove.add(e.getKey());
        }
        for (String k : toRemove) { TRACES.remove(k); TRACE_EXPIRE_AT.remove(k); }
    }

    // -------- 工具方法 --------
    static String nowIso() { return LocalDateTime.now().format(FMT); }

    static Step mkStep(int idx, String title, String subtitle) {
        Step s = new Step();
        s.index = idx;
        s.title = (idx) + ". " + title;
        s.subtitle = subtitle;
        s.status = "pending";
        return s;
    }

    static void markStart(Step s) {
        s.status = "running";
        s.startedAt = nowIso();
    }

    static void markDone(Step s, long durationMs, Object input, Object output, String note) {
        s.status = "done";
        s.finishedAt = nowIso();
        s.durationMs = durationMs;
        s.input = input;
        s.output = output;
        s.note = note;
    }

    static String uid(String prefix) {
        return prefix + "-" + UUID.randomUUID().toString().replace("-", "").substring(0, 12);
    }

    /** 7 个功能的步骤编排（步骤标题对应各功能在 AI 服务中的真实实现，非模拟文案）。注意：最后一步必须放"落快照 + last=true"。 */
    static List<Step> planSteps(String funcType) {
        List<Step> list = new CopyOnWriteArrayList<>();
        int i = 0;
        switch (funcType == null ? "" : funcType) {
            case "article":
                // 科普文章：B 流水线（pipeline_v32：知识库检索→联网→本地搭框架→云端外扩→溯源→校验→拆分三版）
                list.add(mkStep(++i, "请求入队", "接收 funcType=article, topic, target_crowd, persona"));
                list.add(mkStep(++i, "聚合最近用户画像", "从 user 表真实读取：年龄/性别/人群标签/身高体重"));
                list.add(mkStep(++i, "Stage 0 知识库检索", "向量召回 topic 相关权威片段（PubMed/官方指南/权威报告），来源带标签"));
                list.add(mkStep(++i, "Stage 0.5 联网搜索", "按主题在白名单站源检索 ≤10 篇科学文献，标注来源"));
                list.add(mkStep(++i, "Stage 1 本地模型搭骨架", "本地 Ollama(qwen2.5-7b) 只输出 标题+分节标记+速读/深度/综述三档空骨架"));
                list.add(mkStep(++i, "Stage 2 云端模型外扩", "DeepSeek 依据骨架与知识库卡片填充正文（B流水线）"));
                list.add(mkStep(++i, "Stage 2.5/3 溯源校验", "PMID 真实性核对 + 五道格式校验（标题/术语/敏感词/字数/顺序）"));
                list.add(mkStep(++i, "拆分三版并落库", "ArticleSplitUtil 复用线上拆分：short/medium/long 三档，写 AI 快照"));
                break;
            case "recipe":
                // 食材菜谱推荐：真实调用 POST /food/recommend（AI 服务内部 mode_router A/C 决策链由 trace 断点动态展开）
                list.add(mkStep(++i, "请求入队", "接收 ingredients + crowd_type + goal + high_performance"));
                list.add(mkStep(++i, "读取用户画像", "从 user 表真实读取：年龄/性别/人群标签/身高体重"));
                list.add(mkStep(++i, "知识库向量检索", "调用 POST /api/v1/retrieve 召回参考知识片段（供 Prompt 使用）"));
                list.add(mkStep(++i, "Prompt 组装", "系统提示 + 用户画像 + 检索参考 + 功能要求拼装为请求"));
                list.add(mkStep(++i, "调用食谱推荐服务", "POST /food/recommend，AI 服务内部决策链见下方断点"));
                list.add(mkStep(++i, "最终输出校验", "生成文本非空、无模型错误、长度达标"));
                list.add(mkStep(++i, "写 AI 快照，返回可预览 snapshotId", "落 ai_preview_snapshot 表"));
                break;
            case "dietPlan":
                // 一日饮食方案：真实调用 POST /diet/plan（内部 mode_router A/C 决策链由 trace 展开）
                list.add(mkStep(++i, "请求入队", "接收 goal + user_profile + high_performance"));
                list.add(mkStep(++i, "用户画像与身体指标", "读取 user 表，推导 BMI / BMR / TDEE（Mifflin-St Jeor 公式）"));
                list.add(mkStep(++i, "知识库向量检索", "调用 POST /api/v1/retrieve 召回参考知识片段（供 Prompt 使用）"));
                list.add(mkStep(++i, "Prompt 组装", "系统提示 + 用户画像 + 检索参考 + 功能要求拼装为请求"));
                list.add(mkStep(++i, "调用膳食计划服务", "POST /diet/plan，AI 服务内部决策链见下方断点"));
                list.add(mkStep(++i, "最终输出校验", "生成文本非空、无模型错误、长度达标"));
                list.add(mkStep(++i, "写 AI 快照，返回可预览 snapshotId", "落 ai_preview_snapshot 表"));
                break;
            case "nutrition":
                // 营养分析：nutrition_analysis 专用端点（7天饮食聚合→对照指南→缺口诊断→建议）
                list.add(mkStep(++i, "请求入队", "接收 user_profile + 7 天饮食记录"));
                list.add(mkStep(++i, "拉取 7 天饮食流水", "按 userId 聚合 diet_item/diet_meal 各营养素摄入"));
                list.add(mkStep(++i, "营养素汇总", "热量/蛋白质/碳水/脂肪/膳食纤维/钙/叶酸/DHA 逐项累计"));
                list.add(mkStep(++i, "与膳食指南对照", "BMR 比值、宏量营养素占比、微量营养素参考摄入对照"));
                list.add(mkStep(++i, "缺口与超标诊断", "输出优势项/不足项/慢病风险提示"));
                list.add(mkStep(++i, "生成补全建议", "针对每个缺口给出推荐食物与摄入建议"));
                list.add(mkStep(++i, "写 AI 快照，返回可预览 snapshotId", "落 ai_preview_snapshot 表"));
                break;
            case "training":
                // 个性化运动方案：真实调用 POST /exercise/advice（内部 mode_router A/C 决策链由 trace 展开）
                list.add(mkStep(++i, "请求入队", "接收 goal + preferences + user_profile + high_performance"));
                list.add(mkStep(++i, "读取用户画像", "从 user 表真实读取：年龄/性别/人群标签/慢病限制"));
                list.add(mkStep(++i, "知识库向量检索", "调用 POST /api/v1/retrieve 召回参考知识片段（供 Prompt 使用）"));
                list.add(mkStep(++i, "Prompt 组装", "系统提示 + 用户画像 + 检索参考 + 功能要求拼装为请求"));
                list.add(mkStep(++i, "调用运动方案服务", "POST /exercise/advice，AI 服务内部决策链见下方断点"));
                list.add(mkStep(++i, "最终输出校验", "生成文本非空、无模型错误、长度达标"));
                list.add(mkStep(++i, "写 AI 快照，返回可预览 snapshotId", "落 ai_preview_snapshot 表"));
                break;
            case "weeklyReport":
                // 健康周报：weekly_report 端点（周数据聚合→本地大模型分析→图表→文章推荐）
                list.add(mkStep(++i, "请求入队", "接收 user_profile + 本周统计数据"));
                list.add(mkStep(++i, "拉取周数据", "本周饮食/运动/体重/营养达标 5 个域数据聚合"));
                list.add(mkStep(++i, "汇总统计", "体重趋势(含预测)、BMR 摄入比、营养达标率、运动完成度"));
                list.add(mkStep(++i, "本地大模型生成分析", "Ollama(qwen2.5-7b) 生成总结/问题/下周建议"));
                list.add(mkStep(++i, "图表数据生成", "周体重/热量/蛋白质曲线 + 达标环图数据"));
                list.add(mkStep(++i, "科普文章主题匹配推荐", "按本周营养短板匹配知识库科普文章，无匹配回退人群相关文章"));
                list.add(mkStep(++i, "写 AI 快照，返回可预览 snapshotId", "落 ai_preview_snapshot 表"));
                break;
            case "consult":
                // AI 健康咨询：真实调用 POST /chat（AI 服务内部 orchestrator→mode_router 决策链由 trace 展开）
                list.add(mkStep(++i, "请求入队", "接收 message + user_id + health_snapshot"));
                list.add(mkStep(++i, "读取用户画像", "从 user 表真实读取：年龄/性别/人群标签/身高体重"));
                list.add(mkStep(++i, "知识库向量检索", "调用 POST /api/v1/retrieve 召回参考知识片段（供 Prompt 使用）"));
                list.add(mkStep(++i, "Prompt 组装", "七模块上下文：用户画像/身体指标/7天趋势/饮食/运动/参考知识/意图"));
                list.add(mkStep(++i, "调用 AI 健康咨询服务", "POST /chat，AI 服务内部决策链见下方断点"));
                list.add(mkStep(++i, "引用与免责声明注入", "追加参考文献来源 + 非医疗建议声明"));
                list.add(mkStep(++i, "写 AI 快照，返回可预览 snapshotId", "落 ai_preview_snapshot 表"));
                break;
            default:
                list.add(mkStep(++i, "请求受理", "未知 funcType，按通用流程演示"));
                list.add(mkStep(++i, "参数校验", "检查必填项"));
                list.add(mkStep(++i, "执行模拟处理", "sleep 模拟耗时"));
                list.add(mkStep(++i, "写入 AI 快照，返回可预览 snapshotId", ""));
        }
        // 把最后一步标为 last
        list.get(list.size() - 1).last = true;
        return list;
    }

}
