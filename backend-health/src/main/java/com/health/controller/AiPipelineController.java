package com.health.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.health.dto.ApiResponse;
import com.health.entity.AiPreviewSnapshot;
import com.health.entity.User;
import com.health.service.AiChatClientService;
import com.health.service.AiPreviewService;
import com.health.service.ProfileService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import javax.annotation.PostConstruct;
import java.util.*;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * 管理员流程演示页 · 后端 AI 生成流水线【真实执行】控制器。
 *
 * <p>与旧的"模拟 sleep + 假数据"版本不同，本版每一步都调用真实后端能力：</p>
 * <ol>
 *   <li>步骤1 请求入队：接收参数（funcType / mode / userId / topic / payload 骨架）</li>
 *   <li>步骤2 用户画像：真实读取 user 表（userId 给定）→ 年龄/性别/身高/体重/人群/BMI</li>
 *   <li>步骤3 知识库检索：真实调用 AI 服务 POST /api/v1/retrieve（向量召回）</li>
 *   <li>步骤4 Prompt 组装：真实拼接 系统提示 + 画像 + 检索参考 + 主题</li>
 *   <li>步骤5 大模型生成：真实调用 AI 服务对应端点（文章母稿/膳食计划/营养分析/运动建议/周报/咨询/食谱）</li>
 *   <li>步骤6 结果校验：真实校验 文本非空 / 模型错误 / 长度阈值</li>
 *   <li>步骤7 快照落库：真实写 ai_preview_snapshot（payload 与前端骨架融合真实生成内容）</li>
 * </ol>
 *
 * <p>接口：</p>
 * <ul>
 *   <li>POST /api/admin/preview/pipeline/start —— 启动真实流水线，立即返回 traceId</li>
 *   <li>GET  /api/admin/preview/pipeline/trace/{traceId} —— 轮询步骤（每步真实 input/output/耗时）</li>
 *   <li>GET  /api/admin/preview/pipeline/list —— 列出本会话 trace</li>
 * </ul>
 */
@RestController
@RequestMapping("/api/admin/preview/pipeline")
@PreAuthorize("hasRole('ADMIN')")
public class AiPipelineController {

    private final AiPreviewService aiPreviewService;
    private final ProfileService profileService;
    private final AiChatClientService aiChatClient;
    private final ObjectMapper om = new ObjectMapper();

    /** 后台线程池：真实 LLM 调用可能耗时较长（最长 300s），用 4 线程避免串行排队。 */
    private final ScheduledExecutorService worker = Executors.newScheduledThreadPool(4, r -> {
        Thread t = new Thread(r, "ai-pipeline-worker");
        t.setDaemon(true);
        return t;
    });

    public AiPipelineController(AiPreviewService aiPreviewService,
                                ProfileService profileService,
                                AiChatClientService aiChatClient) {
        this.aiPreviewService = aiPreviewService;
        this.profileService = profileService;
        this.aiChatClient = aiChatClient;
    }

    @PostConstruct
    public void initCleaner() {
        worker.scheduleAtFixedRate(AiPipelineEngine::cleanExpired, 10, 10, TimeUnit.MINUTES);
    }

    /** 1) 启动真实流水线。body 与 saveSnapshot 兼容：{ sessionId?, userId?, funcType, mode?, title?, summary?, payload } */
    @PostMapping("/start")
    public ResponseEntity<ApiResponse<Map<String, Object>>> start(@RequestBody(required = false) Map<String, Object> body) {
        if (body == null) {
            return ResponseEntity.badRequest().body(ApiResponse.<Map<String, Object>>error("body 必填"));
        }
        Object payloadObj = body.get("payload");
        if (payloadObj == null) {
            return ResponseEntity.badRequest().body(ApiResponse.<Map<String, Object>>error("payload 必填（完整前端权威组件 JSON，作为骨架与真实生成内容融合）"));
        }
        String funcType = (String) body.get("funcType");
        if (funcType == null || funcType.trim().isEmpty()) {
            return ResponseEntity.badRequest().body(ApiResponse.<Map<String, Object>>error("funcType 必填"));
        }
        String sessionId = (String) body.get("sessionId");
        if (sessionId == null || sessionId.trim().isEmpty()) {
            sessionId = "s-" + UUID.randomUUID().toString().replace("-", "").substring(0, 12);
        }
        String mode = (String) body.get("mode");
        if (mode == null || mode.trim().isEmpty()) mode = "normal";
        Integer userId = null;
        Object u = body.get("userId");
        if (u instanceof Number) userId = ((Number) u).intValue();
        String title = (String) body.get("title");
        String summary = (String) body.get("summary");

        AiPipelineEngine.Trace t = new AiPipelineEngine.Trace();
        t.traceId = AiPipelineEngine.uid("tr");
        t.funcType = funcType;
        t.sessionId = sessionId;
        t.mode = mode;
        t.userId = userId;
        t.createdAt = AiPipelineEngine.nowIso();
        t.steps = AiPipelineEngine.planSteps(funcType);
        AiPipelineEngine.TRACES.put(t.traceId, t);
        AiPipelineEngine.touch(t.traceId);

        final String payloadJson;
        try { payloadJson = om.writeValueAsString(payloadObj); }
        catch (Exception e) {
            return ResponseEntity.badRequest().body(ApiResponse.<Map<String, Object>>error("payload JSON 序列化失败: " + e.getMessage()));
        }
        final String fSessionId = sessionId;
        final Integer fUserId = userId;
        final String fMode = mode;
        final String fTitle = title;
        final String fSummary = summary;
        worker.submit(() -> runPipeline(t, fSessionId, fUserId, fMode, fTitle, fSummary, payloadObj, payloadJson));

        Map<String, Object> out = new LinkedHashMap<>();
        out.put("traceId", t.traceId);
        out.put("funcType", t.funcType);
        out.put("sessionId", t.sessionId);
        out.put("mode", t.mode);
        out.put("createdAt", t.createdAt);
        out.put("totalSteps", t.steps.size());
        out.put("done", false);
        out.put("steps", snapshotStepsMeta(t.steps));
        return ResponseEntity.ok(ApiResponse.success(out));
    }

    /** 2) 轮询 trace：返回当前已完成 + 进行中的步骤（含真实 input/output/耗时）。 */
    @GetMapping("/trace/{traceId}")
    public ResponseEntity<ApiResponse<Map<String, Object>>> pollTrace(@PathVariable String traceId) {
        AiPipelineEngine.Trace t = AiPipelineEngine.TRACES.get(traceId);
        if (t == null) return ResponseEntity.status(404).body(ApiResponse.<Map<String, Object>>error("trace not found: " + traceId));
        AiPipelineEngine.touch(traceId);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("traceId", t.traceId);
        out.put("funcType", t.funcType);
        out.put("sessionId", t.sessionId);
        out.put("mode", t.mode);
        out.put("createdAt", t.createdAt);
        out.put("totalSteps", t.steps.size());
        out.put("done", t.done);
        out.put("error", t.error);
        out.put("finalSnapshotId", t.finalSnapshotId);
        out.put("steps", t.steps);
        return ResponseEntity.ok(ApiResponse.success(out));
    }

    /** 3) 列 trace（方便调试/展示"最近跑过的流水线"） */
    @GetMapping("/list")
    public ResponseEntity<ApiResponse<List<Map<String, Object>>>> listTraces(@RequestParam(required = false) String sessionId) {
        List<Map<String, Object>> out = new ArrayList<>();
        for (AiPipelineEngine.Trace t : AiPipelineEngine.TRACES.values()) {
            if (sessionId != null && !sessionId.equals(t.sessionId)) continue;
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("traceId", t.traceId);
            m.put("funcType", t.funcType);
            m.put("sessionId", t.sessionId);
            m.put("createdAt", t.createdAt);
            m.put("totalSteps", t.steps.size());
            m.put("done", t.done);
            m.put("error", t.error);
            m.put("finalSnapshotId", t.finalSnapshotId);
            out.add(m);
        }
        out.sort((a, b) -> ((String) b.get("createdAt")).compareTo((String) a.get("createdAt")));
        return ResponseEntity.ok(ApiResponse.success(out));
    }

    // ==================== 真实流水线执行 ====================

    private static List<Map<String, Object>> snapshotStepsMeta(List<AiPipelineEngine.Step> steps) {
        List<Map<String, Object>> out = new ArrayList<>();
        for (AiPipelineEngine.Step s : steps) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("index", s.index);
            m.put("title", s.title);
            m.put("subtitle", s.subtitle);
            m.put("status", s.status);
            out.add(m);
        }
        return out;
    }

    /**
     * 依次执行每一步：真实调用 DB / AI 服务，并把每一步的 input/output/note/耗时写到 Step，
     * 前端 300ms 轮询即可看到"真实的后端执行过程"。最后一步真实落 ai_preview_snapshot。
     */
    private void runPipeline(AiPipelineEngine.Trace t, String sessionId, Integer userId, String mode,
                             String title, String summary, Object payloadObj, String payloadJson) {
        try {
            // 贯穿各步骤的"真实上下文"
            Map<String, Object> profile = new LinkedHashMap<>();
            Map<String, Object> retrieved = new LinkedHashMap<>();
            String generatedText = "";
            String aiError = null;
            Map<String, Object> aiStructured = null;
            Map<String, Object> aiMeta = new LinkedHashMap<>();

            int macroPos = 0;
            for (int i = 0; i < t.steps.size(); i++) {
                AiPipelineEngine.Step s = t.steps.get(i);
                // AI 服务返回的真实 trace 断点展开的步骤（autoDone）已执行完毕，直接跳过位置映射
                if (s.autoDone) continue;
                AiPipelineEngine.markStart(s);
                long t0 = System.currentTimeMillis();
                Object input = null;
                Object output = null;
                String note = "";
                try {
                    // 步骤按"位置 + 最后一步"映射真实动作，兼容 7 步与 8 步（weeklyReport/consult）编排：
                    // pos 1 入队 → 2 画像 → 3 检索 → 4 Prompt → 5 生成 → 6 校验 → (7 补充:引用/图表) → last 落库
                    boolean isLast = s.last;
                    int pos = ++macroPos;
                if (isLast) {
                    // 最后一步：真实落 ai_preview_snapshot（骨架 payload 与真实生成内容融合）
                    Map<String, Object> realPayload = buildRealPayload(t.funcType, payloadObj, generatedText, aiError, retrieved, aiStructured);
                    String finalJson = om.writeValueAsString(realPayload);
                    input = mapOf("targetTable", "ai_preview_snapshot", "funcType", t.funcType, "payloadBytes", finalJson.length());
                    AiPreviewSnapshot snap = new AiPreviewSnapshot();
                    snap.setSessionId(sessionId);
                    snap.setUserId(userId);
                    snap.setFuncType(t.funcType);
                    snap.setMode(mode);
                    snap.setTitle(titleOf(realPayload, title));
                    snap.setSummary(summaryOf(realPayload, summary));
                    snap.setPayloadJson(finalJson);
                    snap = aiPreviewService.save(snap);
                    t.finalSnapshotId = String.valueOf(snap.getId());
                    output = mapOf("snapshotId", snap.getId(), "funcType", snap.getFuncType(), "sessionId", snap.getSessionId(),
                            "payloadBytes", finalJson.length(), "savedAt", AiPipelineEngine.nowIso());
                    note = "已持久化到 ai_preview_snapshot 表（id = " + snap.getId() + "）。下一步：前端 1:1 预览 → 点喜欢+发布。";
                } else if (pos == 1) {
                    input = mapOf(
                            "funcType", t.funcType,
                            "mode", mode,
                            "userId", userId,
                            "topic", topicOf(t.funcType, payloadObj),
                            "payloadKeys", sampleKeys(payloadObj, 10),
                            "payloadBytes", payloadJson.length());
                    output = mapOf("requestId", AiPipelineEngine.uid("req"), "accepted", true, "queue", "ai-pipeline-worker");
                    note = "请求已入队，进入 AI 编排层。";
                } else if (pos == 2) {
                    input = mapOf("userId", userId, "targetTables", Arrays.asList("user", "body_metrics_history"));
                    profile = loadProfile(userId);
                    output = profile;
                    note = "missing".equals(profile.get("source"))
                            ? "未绑定真实用户（userId=" + userId + "）：未编造画像，请在左侧选择测试用户后重跑。"
                            : "已从数据库真实读取用户画像（userId=" + userId + "）。";
                } else if (pos == 3) {
                    String query = topicOf(t.funcType, payloadObj);
                    String crowd = crowdOf(profile);
                    input = mapOf("endpoint", "POST /api/v1/retrieve", "query", query, "top_k", 6, "target_crowd", crowd, "embeddingModel", "bge-base-zh-v1.5");
                    retrieved = retrieve(query, crowd);
                    output = mapOf("total", retrieved.get("total"), "hits", retrieved.get("hits"));
                    note = "真实向量召回命中 " + retrieved.get("total") + " 条知识库片段。";
                } else if (pos == 4) {
                    String prompt = buildPrompt(t.funcType, payloadObj, profile, retrieved);
                    input = mapOf("funcType", t.funcType, "assembledFrom", Arrays.asList("system-prompt", "user-profile", "kb-references", "topic"));
                    output = mapOf("promptLength", prompt.length(), "promptChars", truncate(prompt, 600));
                    note = "Prompt 已组装（" + prompt.length() + " 字符，含真实检索参考）。";
                } else if (pos == 5) {
                    String endpoint = aiEndpoint(t.funcType);
                    input = mapOf("endpoint", endpoint, "mode", mode,
                            "requestKeys", Arrays.asList(sampleKeys(requestBodyFor(t.funcType, payloadObj), 4)));
                    Generation gen = callLlm(t.funcType, userId, mode, payloadObj, profile);
                    generatedText = gen.text;
                    aiError = gen.error;
                    aiStructured = gen.structured;
                    aiMeta = gen.meta == null ? new LinkedHashMap<>() : gen.meta;
                    Map<String, Object> genOut = new LinkedHashMap<>();
                    genOut.put("text", truncate(generatedText, 500));
                    genOut.put("length", generatedText.length());
                    genOut.put("modelError", aiError);
                    if (gen.structured != null) {
                        genOut.put("structuredKeys", gen.structured.keySet());
                        genOut.put("route", gen.meta.get("route"));
                        genOut.put("aiMode", gen.meta.get("mode"));
                    }
                    if (gen.tokens != null) {
                        genOut.put("tokens", gen.tokens);
                        s.extra = gen.tokens; // 步骤附加信息：token 消耗明细（本地/云端）
                    }
                    output = genOut;
                    note = (aiError != null && !aiError.trim().isEmpty())
                            ? "⚠️ 大模型调用失败（" + aiError + "），已降级用骨架数据呈现。"
                            : "大模型真实生成 " + generatedText.length() + " 字"
                            + (gen.tokens != null ? "；Token 消耗见步骤详情（本地/云端）。" : "。");
                    // 把 AI 服务返回的真实 trace 断点（mode_router A/C 决策链）展开为流水线步骤
                    // 每个断点带真实中间数据与成功/失败判断，插入到"调用 AI 服务"步骤之后、最终校验之前
                    insertTraceBreakpoints(t, i, aiMeta);
                } else if (pos == 6) {
                    input = mapOf("textLength", generatedText.length(), "rules", Arrays.asList("nonEmpty", "modelErrorFree", "minLength>=20"));
                    Map<String, Object> chk = validate(generatedText, aiError);
                    output = chk;
                    note = Boolean.TRUE.equals(chk.get("pass")) ? "校验通过：" + chk.get("detail") : "校验提示：" + chk.get("detail");
                } else {
                    // 8 步编排中多出的中间步骤（weeklyReport=生成图表数据 / consult=引用&免责注入）
                    List<Object> refs = new ArrayList<>();
                    Object hits = retrieved.get("hits");
                    if (hits instanceof List) {
                        for (Object h : (List<?>) hits) {
                            if (h instanceof Map && ((Map<?, ?>) h).get("source") != null) {
                                refs.add(((Map<?, ?>) h).get("source").toString());
                            }
                        }
                    }
                    input = mapOf("sources", refs, "basedOn", "步骤3检索结果");
                    output = mapOf("refCount", refs.size(), "sources", refs, "disclaimer", "非医疗建议声明已注入");
                    note = "引用来源与免责声明已注入（" + refs.size() + " 条，来自真实检索结果）。";
                }
                } catch (Throwable e) {
                    output = mapOf("error", e.getClass().getSimpleName() + ": " + e.getMessage());
                    note = "步骤执行异常（已跳过，不阻断流水线）：" + e.getMessage();
                }
                long dt = Math.max(1L, System.currentTimeMillis() - t0);
                AiPipelineEngine.markDone(s, dt, input, output, note);
            }
            t.done = true;
        } catch (Throwable e) {
            t.done = true;
            t.error = e.getClass().getSimpleName() + ": " + e.getMessage();
        } finally {
            AiPipelineEngine.touch(t.traceId);
        }
    }

    // ==================== 真实数据读取 ====================

    /** 步骤2：真实读取用户画像；userId 缺失/不存在时返回缺失标记（不编造默认画像）。 */
    private Map<String, Object> loadProfile(Integer userId) {
        Map<String, Object> p = new LinkedHashMap<>();
        if (userId == null || userId <= 0) {
            p.put("source", "missing");
            p.put("note", "未选择用户。请先在左侧选择测试用户（user001-006 / test001-003），再重新执行流水线。");
            return p;
        }
        User u = profileService.getProfile(userId);
        if (u == null) {
            p.put("source", "missing");
            p.put("note", "userId=" + userId + " 不存在，请选择左侧示例用户后重跑。");
            return p;
        }
        p.put("source", "db");
        p.put("userId", u.getUserId());
        p.put("username", u.getUsername());
        p.put("gender", u.getGender());
        p.put("age", u.getAge());
        p.put("height", u.getHeight());
        p.put("weight", u.getWeight());
        p.put("crowdType", u.getCrowdType());
        p.put("tastePreference", u.getTastePreference());
        if (u.getAllergicFoods() != null && !u.getAllergicFoods().trim().isEmpty()) p.put("allergicFoods", u.getAllergicFoods());
        if (u.getDietaryRestrictions() != null && !u.getDietaryRestrictions().trim().isEmpty()) p.put("dietaryRestrictions", u.getDietaryRestrictions());
        if (u.getHeight() != null && u.getWeight() != null && u.getHeight() > 0) {
            double hm = u.getHeight() / 100.0;
            p.put("bmi", Math.round(u.getWeight() / (hm * hm) * 10.0) / 10.0);
        }
        return p;
    }

    /** 步骤3：真实调用 AI 服务 /api/v1/retrieve 做向量召回。 */
    private Map<String, Object> retrieve(String query, String crowd) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("query", query);
        body.put("top_k", 6);
        body.put("target_crowd", crowd);
        Map<String, Object> resp = aiChatClient.postForMapLongKeepMeta("/retrieve", body, "知识库检索");
        List<Object> hits = new ArrayList<>();
        Object results = resp.get("results");
        if (results instanceof List) {
            for (Object item : (List<?>) results) {
                if (item instanceof Map) {
                    Map<?, ?> m = (Map<?, ?>) item;
                    Map<String, Object> hit = new LinkedHashMap<>();
                    Object md = m.get("metadata");
                    String source = "";
                    String topic = "";
                    if (md instanceof Map) {
                        Map<?, ?> mm = (Map<?, ?>) md;
                        if (mm.get("source") != null) source = mm.get("source").toString();
                        if (mm.get("topic") != null) topic = mm.get("topic").toString();
                        if (source.isEmpty() && mm.get("source_channel") != null) source = mm.get("source_channel").toString();
                    }
                    if (source.isEmpty()) source = "知识库";
                    hit.put("title", topic.isEmpty() ? truncate(m.get("content"), 24) : topic);
                    hit.put("source", source);
                    hit.put("rerankScore", m.get("rerank_score"));
                    hit.put("excerpt", truncate(m.get("content"), 160));
                    hits.add(hit);
                }
            }
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("total", hits.size());
        out.put("hits", hits);
        return out;
    }

    /** 步骤4：真实组装 Prompt。 */
    private String buildPrompt(String funcType, Object payload, Map<String, Object> profile, Map<String, Object> retrieved) {
        StringBuilder sb = new StringBuilder();
        sb.append("【系统】你是资深健康科普与健康管理助手，输出需严谨、可执行、符合医疗合规。\n");
        sb.append("【功能类型】").append(funcType).append("\n");
        sb.append("【用户画像】").append(profile.toString()).append("\n");
        sb.append("【主题/需求】").append(topicOf(funcType, payload)).append("；").append(questionOf(payload)).append("\n");
        sb.append("【知识库参考】");
        Object hits = retrieved.get("hits");
        if (hits instanceof List) {
            List<?> list = (List<?>) hits;
            for (int i = 0; i < Math.min(list.size(), 4); i++) {
                Object h = list.get(i);
                if (h instanceof Map) {
                    Object ex = ((Map<?, ?>) h).get("excerpt");
                    if (ex != null) sb.append("\n  - ").append(ex);
                }
            }
        }
        sb.append("\n【要求】结合以上真实数据作答，给出分条建议。");
        return sb.toString();
    }

    /** 步骤5：按功能类型真实调用 AI 服务对应端点（300s 长超时模板）。 */
    private Generation callLlm(String funcType, Integer userId, String mode, Object payload, Map<String, Object> profile) {
        Map<String, Object> body = new LinkedHashMap<>();
        try {
            switch (funcType) {
                case "article":
                    body.put("topic", topicOf(funcType, payload));
                    body.put("target_crowd", crowdOf(profile));
                    return parseGen(aiChatClient.postForMapLongKeepMeta("/articles/mother-draft", body, "文章母稿生成(B方案)"));
                case "recipe":
                    body.put("ingredients", firstList(payload, "ingredients", Arrays.asList("鸡胸肉", "西兰花", "藜麦", "鸡蛋", "西红柿")));
                    body.put("crowd_type", crowdOf(profile));
                    body.put("goal", str(payload, "goal", "健康饮食"));
                    body.put("high_performance", "high_performance".equals(mode));
                    body.put("user_profile", profileToAi(profile));
                    return parseGen(aiChatClient.postForMapLongKeepMeta("/food/recommend", body, "食谱推荐生成"));
                case "dietPlan":
                    body.put("user_profile", profileToAi(profile));
                    body.put("goal", str(payload, "goal", "减脂"));
                    body.put("high_performance", "high_performance".equals(mode));
                    return parseGen(aiChatClient.postForMapLongKeepMeta("/diet/plan", body, "膳食计划生成"));
                case "nutrition":
                    body.put("user_profile", profileToAi(profile));
                    body.put("daily_nutrition", payload instanceof Map && ((Map<?, ?>) payload).get("daily_nutrition") != null
                            ? ((Map<?, ?>) payload).get("daily_nutrition") : new LinkedHashMap<>());
                    body.put("daily_exercise", new LinkedHashMap<>());
                    return parseGen(aiChatClient.postForMapLongKeepMeta("/nutrition/analyze", body, "营养分析生成"));
                case "training":
                    body.put("user_profile", profileToAi(profile));
                    body.put("goal", str(payload, "goal", "保持健康"));
                    body.put("preferences", str(payload, "preferences", "居家可做"));
                    return parseGen(aiChatClient.postForMapLongKeepMeta("/exercise/advice", body, "运动方案生成"));
                case "weeklyReport":
                    body.put("user_profile", profileToAi(profile));
                    body.put("weekly_stats", new LinkedHashMap<>());
                    return parseGen(aiChatClient.postForMapLongKeepMeta("/report/weekly-summary", body, "健康周报生成"));
                default: // consult
                    body.put("message", questionOf(payload));
                    body.put("user_id", userId == null ? 0 : userId);
                    body.put("health_snapshot", profileToAi(profile));
                    body.put("high_performance", "high_performance".equals(mode));
                    return parseGen(aiChatClient.postForMapLongKeepMeta("/chat", body, "AI 健康咨询"));
            }
        } catch (Exception e) {
            return new Generation("", "AI 服务不可达: " + e.getMessage());
        }
    }

    /** 解析 AI 服务统一响应 {success, code, message, data:{response,...}} 或 agent 顶层 {response,...}。 */
    @SuppressWarnings("unchecked")
    private Generation parseGen(Map<String, Object> resp) {
        if (resp == null) return new Generation("", "AI 服务返回空响应");
        Object err = resp.get("error");
        if (err != null && !err.toString().trim().isEmpty() && !"None".equals(err.toString().trim())) {
            return new Generation("", err.toString());
        }
        if (Boolean.FALSE.equals(resp.get("success"))) {
            Object msg = resp.get("message");
            return new Generation("", msg == null ? "AI 服务处理失败" : msg.toString());
        }
        // data.response 可能是字符串（文章/咨询）也可能是结构化 dict（膳食/食谱/运动/营养/周报）；
        // 部分 agent 直接返回顶层结构化 dict（如 /food/recommend 的 {total_meals, meal_plan, _meta}），需兜底识别。
        Object responseObj = null;
        Object dataObj = resp.get("data");
        if (dataObj instanceof Map) {
            responseObj = ((Map<?, ?>) dataObj).get("response");
            if (responseObj == null) responseObj = dataObj;
        } else {
            responseObj = resp.get("response");
        }
        if (responseObj == null) {
            // 顶层即业务结果：剔除包装字段后仍非空，则整体视为结构化结果
            Map<String, Object> stripped = new LinkedHashMap<>();
            for (Map.Entry<String, Object> e : resp.entrySet()) {
                String k = e.getKey();
                if ("success".equals(k) || "code".equals(k) || "message".equals(k)
                        || "error".equals(k) || "data".equals(k) || "_meta".equals(k) || "tokens".equals(k)) {
                    continue;
                }
                if (e.getValue() != null) stripped.put(k, e.getValue());
            }
            if (!stripped.isEmpty()) responseObj = stripped;
        }
        String text = "";
        Map<String, Object> structured = null;
        if (responseObj instanceof Map) {
            structured = (Map<String, Object>) responseObj;
            try { text = om.writeValueAsString(structured); } catch (Exception e) { text = structured.toString(); }
        } else if (responseObj != null) {
            text = responseObj.toString();
        }
        if (text.trim().isEmpty()) {
            Object msg = resp.get("message");
            if (msg != null && !msg.toString().trim().isEmpty()) return new Generation(msg.toString(), null);
            return new Generation("", "AI 服务返回内容为空");
        }
        // _meta（route/mode/trace）透传给前端流水线：可能在 data 里，也可能在顶层（顶层结构化返回）
        Map<String, Object> meta = new LinkedHashMap<>();
        Object metaObj = resp.get("_meta");
        if (metaObj instanceof Map) {
            meta = (Map<String, Object>) metaObj;
        } else if (dataObj instanceof Map) {
            Object m = ((Map<?, ?>) dataObj).get("_meta");
            if (m instanceof Map) meta = (Map<String, Object>) m;
        }
        return new Generation(text, null, extractTokens(resp), structured, meta);
    }

    /** 从 AI 服务响应中提取 token 明细（本地/云端区分），无则返回 null。 */
    @SuppressWarnings("unchecked")
    private Map<String, Object> extractTokens(Map<String, Object> resp) {
        try {
            Object data = resp.get("data");
            if (data instanceof Map) {
                Object t = ((Map<?, ?>) data).get("tokens");
                if (t instanceof Map) return (Map<String, Object>) t;
            }
            Object t2 = resp.get("tokens");
            if (t2 instanceof Map) return (Map<String, Object>) t2;
        } catch (Exception ignored) {
        }
        return null;
    }

    /** 步骤6：真实校验。 */
    private Map<String, Object> validate(String text, String aiError) {
        Map<String, Object> r = new LinkedHashMap<>();
        boolean nonEmpty = text != null && !text.trim().isEmpty();
        boolean noError = aiError == null || aiError.trim().isEmpty();
        int len = text == null ? 0 : text.trim().length();
        boolean lengthOk = nonEmpty && len >= 20;
        r.put("textLength", len);
        r.put("nonEmpty", nonEmpty);
        r.put("modelErrorFree", noError);
        r.put("lengthOk", lengthOk);
        r.put("pass", nonEmpty && noError && lengthOk);
        r.put("detail", !nonEmpty ? "生成内容为空" : (noError ? "内容长度 " + len + " 字，无模型错误" : "模型调用失败，已降级"));
        return r;
    }

    /**
     * 步骤5（调用 AI 服务）之后：把 AI 服务返回的真实 trace 断点（mode_router A/C 决策链）展开为流水线步骤。
     * 每个 trace 元素 = {key, step, data}（每阶段的真实中间数据）；断点状态按 data 判断：
     * error 非空 → error；passed=false → 校验未通过（仍展示，供用户看到"走了哪条路"）。
     * 这样前端展示的就是 AI 服务内部真实执行的每一小块 + 成功/失败判断，
     * 而非预定义的"模拟"步骤（模板命中直接返回 / 本地A / 校验失败回退云端C / 入库 都真实呈现）。
     */
    @SuppressWarnings("unchecked")
    private void insertTraceBreakpoints(AiPipelineEngine.Trace t, int afterIndex, Map<String, Object> aiMeta) {
        try {
            Object traceObj = aiMeta.get("trace");
            if (!(traceObj instanceof List)) return;
            List<?> trace = (List<?>) traceObj;
            if (trace.isEmpty()) return;
            List<AiPipelineEngine.Step> inserted = new ArrayList<>();
            int idx = afterIndex + 1;
            for (Object o : trace) {
                if (!(o instanceof Map)) continue;
                Map<?, ?> tm = (Map<?, ?>) o;
                Object stepName = tm.get("step");
                if (stepName == null || stepName.toString().trim().isEmpty()) continue;
                String name = stepName.toString();
                AiPipelineEngine.Step ts = AiPipelineEngine.mkStep(idx, name, "AI 服务内部真实断点（mode_router 中间数据）");
                ts.index = idx;
                Object d = tm.get("data");
                ts.input = mapOf("key", tm.get("key"), "breakpoint", "mode_router.trace");
                ts.output = d;
                ts.startedAt = AiPipelineEngine.nowIso();
                ts.finishedAt = AiPipelineEngine.nowIso();
                ts.autoDone = true;
                // 断点成功/失败判断（真实中间数据）
                boolean failed = false;
                String failReason = "";
                if (d instanceof Map) {
                    Object err = ((Map<?, ?>) d).get("error");
                    if (err != null && !err.toString().trim().isEmpty()) {
                        failed = true;
                        failReason = err.toString();
                    }
                    if (Boolean.FALSE.equals(((Map<?, ?>) d).get("passed"))) {
                        failed = true;
                        Object issues = ((Map<?, ?>) d).get("issues");
                        if (failReason.isEmpty() && issues instanceof List && !((List<?>) issues).isEmpty()) {
                            failReason = "校验未通过：" + issues;
                        }
                    }
                }
                ts.status = failed ? "error" : "done";
                ts.note = failed
                        ? "断点未通过：" + (failReason.length() > 150 ? failReason.substring(0, 150) : failReason)
                        : "断点执行成功（真实中间数据见输出）";
                inserted.add(ts);
                idx++;
            }
            if (inserted.isEmpty()) return;
            // 插入到"调用 AI 服务"步骤之后，并整体重编号（last 落库步骤保持在最后）
            t.steps.addAll(afterIndex + 1, inserted);
            renumberSteps(t.steps);
        } catch (Exception e) {
            // trace 展开失败不阻断流水线：加一个提示断点
            AiPipelineEngine.Step s2 = AiPipelineEngine.mkStep(afterIndex + 1, "AI 服务内部断点展开",
                    "trace 解析失败，已忽略");
            s2.status = "error";
            s2.autoDone = true;
            s2.note = "trace 展开异常：" + e.getMessage();
            t.steps.add(afterIndex + 1, s2);
            renumberSteps(t.steps);
        }
    }

    /** 按步骤顺序重编号 index 与 title 前缀（trace 断点插入后调用）。 */
    private void renumberSteps(List<AiPipelineEngine.Step> steps) {
        int idx = 1;
        for (AiPipelineEngine.Step s : steps) {
            s.index = idx;
            int sp = s.title.indexOf(". ");
            if (sp > 0) s.title = idx + s.title.substring(sp);
            idx++;
        }
    }

    /** 步骤7：把真实 AI 生成内容（结构化结果）转换为 viewer 可渲染的 payload；AI 失败才用骨架兜底。 */
    @SuppressWarnings("unchecked")
    private Map<String, Object> buildRealPayload(String funcType, Object skeleton, String text, String aiError,
                                                 Map<String, Object> retrieved, Map<String, Object> aiStructured) {
        Map<String, Object> p = new LinkedHashMap<>();
        if (skeleton instanceof Map) p.putAll((Map<String, Object>) skeleton);
        p.put("__ai_real", true);

        boolean modelOk = text != null && !text.trim().isEmpty() && (aiError == null || aiError.trim().isEmpty());
        Map<String, Object> s = aiStructured == null ? new LinkedHashMap<>() : aiStructured;

        switch (funcType) {
            case "article": {
                // 复用线上真实拆分脚本 ArticleSplitUtil（与文章管理页一致）：
                // 母稿 → 速读卡/深度文/综述文 三版 + META + 参考文献 + 五道校验
                String topic = str(p, "topic", "健康科普");
                if (modelOk) {
                    com.health.util.ArticleSplitUtil.SplitResult split =
                            com.health.util.ArticleSplitUtil.splitMotherDraft(text, crowdOf(null));
                    if (split != null) {
                        p.put("contentShort", split.shortText);
                        p.put("contentMedium", split.mediumText);
                        p.put("contentLong", split.longText);
                        p.put("summary", firstNonEmpty(split.summaries.get("medium"), split.summaries.get("long"),
                                truncate(split.mediumText, 150)));
                        if (!split.meta.isEmpty()) p.put("meta", split.meta);
                        if (!split.refs.isEmpty()) p.put("refs", split.refs);
                        com.health.util.ArticleSplitUtil.ValidationResult vr = com.health.util.ArticleSplitUtil.validate(split);
                        p.put("__validate", mapOf("passed", vr.passed, "score", vr.score, "errors", vr.errors));
                    } else {
                        // 拆分失败：退化用原文
                        p.put("contentMedium", text);
                        p.put("contentShort", text.length() > 600 ? text.substring(0, 600) : text);
                        p.put("contentLong", text);
                        p.put("summary", truncate(text, 150));
                    }
                    List<Object> srcs = new ArrayList<>();
                    Object hits = retrieved.get("hits");
                    if (hits instanceof List) {
                        for (Object h : (List<?>) hits) {
                            if (h instanceof Map) {
                                Object src = ((Map<?, ?>) h).get("source");
                                if (src != null) srcs.add(src.toString());
                            }
                        }
                    }
                    if (!srcs.isEmpty()) p.put("sourcesJson", srcs);
                    p.put("title", str(p, "title", topic + " · AI 生成科普指南"));
                    p.put("wordCount", text.length());
                }
                break;
            }
            case "recipe": {
                // 真实 food_recommend 返回 {meal_plan:[...], total_calories, total_protein, tips, missing_ingredients}
                if (modelOk && !s.isEmpty()) {
                    Object mp = s.get("meal_plan");
                    if (mp instanceof List && !((List<?>) mp).isEmpty()) {
                        p.put("meal_plan", mp);
                        List<Object> first = (List<Object>) mp;
                        if (!first.isEmpty() && first.get(0) instanceof Map) {
                            Map<?, ?> meal0 = (Map<?, ?>) first.get(0);
                            Object name = meal0.get("name");
                            if (name != null) p.put("recipeName", name.toString());
                        }
                    }
                    if (s.get("total_calories") != null) p.put("totalCalories", s.get("total_calories"));
                    if (s.get("total_protein") != null) p.put("totalProtein", s.get("total_protein"));
                    if (s.get("tips") != null) p.put("tips", s.get("tips"));
                    if (s.get("missing_ingredients") != null) p.put("missingIngredients", s.get("missing_ingredients"));
                    String goal = str(p, "goal", "");
                    String crowd = str(p, "crowd_type", str(s, "crowd_type", ""));
                    p.put("description", (crowd.isEmpty() ? "" : crowd + " · ") + (goal.isEmpty() ? "AI 三餐食谱推荐" : goal));
                } else if (modelOk) {
                    p.put("description", truncate(realText(text), 220));
                }
                break;
            }
            case "dietPlan": {
                // 真实 diet_plan 返回 {daily_plan:{breakfast/lunch/dinner/snack 或 早餐/午餐/晚餐/加餐}, total_calories, nutrition_breakdown,...}
                if (modelOk && !s.isEmpty()) {
                    Object dp = s.get("daily_plan");
                    Map<String, Object> plan = dp instanceof Map ? (Map<String, Object>) dp : new LinkedHashMap<>();
                    List<Map<String, Object>> days = new ArrayList<>();
                    Map<String, Object> day = new LinkedHashMap<>();
                    day.put("day", "今日");
                    day.put("breakfast", planMeals(firstOf(plan, "breakfast", "早餐")));
                    day.put("lunch", planMeals(firstOf(plan, "lunch", "午餐")));
                    day.put("dinner", planMeals(firstOf(plan, "dinner", "晚餐")));
                    day.put("snack", planMeals(firstOf(plan, "snack", "加餐")));
                    Object tc = s.get("total_calories");
                    day.put("totalKcal", tc == null ? "≈ 1800 kcal" : tc + " kcal");
                    days.add(day);
                    p.put("days", days);
                    if (tc != null) p.put("targetCalories", tc);
                    Object nb = s.get("nutrition_breakdown");
                    if (nb instanceof Map) {
                        Map<?, ?> nbm = (Map<?, ?>) nb;
                        Object pro = nbm.get("protein"), car = nbm.get("carbohydrate"), fat = nbm.get("fat");
                        if (pro != null) p.put("protein", pro);
                        if (car != null) p.put("carbs", car);
                        if (fat != null) p.put("fat", fat);
                    }
                    Object summary = s.get("summary");
                    if (summary instanceof List) {
                        p.put("summary", joinList((List<?>) summary, "；"));
                    } else if (summary != null) {
                        p.put("summary", summary.toString());
                    } else if (s.get("tips") != null) {
                        Object tips = s.get("tips");
                        p.put("summary", tips instanceof List ? joinList((List<?>) tips, "；") : tips.toString());
                    }
                    p.put("title", str(p, "title", "今日膳食方案"));
                } else if (modelOk) {
                    p.put("summary", truncate(realText(text), 220));
                }
                break;
            }
            case "nutrition": {
                // 真实 nutrition 返回 {nutrition_score, summary, recommendations[], risk_items[], ...}
                if (modelOk && !s.isEmpty()) {
                    if (s.get("summary") != null) p.put("advice", s.get("summary"));
                    if (s.get("recommendations") != null) {
                        List<Object> recs = new ArrayList<>();
                        for (Object r : listOf(s.get("recommendations"))) {
                            if (r instanceof Map) {
                                Object sug = ((Map<?, ?>) r).get("suggestion");
                                if (sug != null) recs.add(sug.toString());
                            }
                        }
                        if (!recs.isEmpty()) p.put("suggestions", recs);
                    }
                    if (s.get("nutrition_ratio") != null) {
                        p.put("analysis", s.get("nutrition_ratio"));
                    }
                    if (s.get("risk_items") != null) p.put("issues", s.get("risk_items"));
                    if (s.get("nutrition_score") != null) p.put("score", s.get("nutrition_score"));
                    p.put("title", str(p, "title", "营养摄入分析"));
                } else if (modelOk) {
                    p.put("advice", truncate(realText(text), 320));
                    p.put("analysis", truncate(realText(text), 200));
                }
                break;
            }
            case "training": {
                // 真实 exercise 返回 {goal, weekly_schedule:[{day,exercise_type,duration,intensity,description,calories_burn_estimate}], warm_up, cool_down, precautions, progression_plan}
                if (modelOk && !s.isEmpty()) {
                    List<Object> weeks = new ArrayList<>();
                    for (Object w : listOf(s.get("weekly_schedule"))) {
                        if (!(w instanceof Map)) continue;
                        Map<?, ?> wm = (Map<?, ?>) w;
                        String day = wm.get("day") == null ? "" : wm.get("day").toString();
                        String etype = wm.get("exercise_type") == null ? "" : wm.get("exercise_type").toString();
                        String dur = wm.get("duration") == null ? "" : wm.get("duration").toString();
                        String desc = wm.get("description") == null ? "" : wm.get("description").toString();
                        boolean rest = day.contains("休息") || etype.contains("休息");
                        Map<String, Object> wcard = new LinkedHashMap<>();
                        wcard.put("day", day);
                        wcard.put("rest", rest);
                        wcard.put("theme", rest ? "休息日" : "训练日");
                        if (!rest) {
                            List<Map<String, Object>> exs = new ArrayList<>();
                            Map<String, Object> ex = new LinkedHashMap<>();
                            ex.put("name", etype);
                            ex.put("duration", dur);
                            ex.put("tip", desc);
                            exs.add(ex);
                            wcard.put("exercises", exs);
                        } else {
                            wcard.put("tip", desc.isEmpty() ? "充分恢复，保持睡眠与营养。" : desc);
                        }
                        weeks.add(wcard);
                    }
                    if (!weeks.isEmpty()) {
                        p.put("weeklyPlan", weeks);
                        if (s.get("goal") != null) p.put("goal", s.get("goal"));
                        p.put("summary", s.get("progression_plan") == null ? "" : s.get("progression_plan").toString());
                        if (s.get("warm_up") != null) p.put("warmUp", s.get("warm_up"));
                        if (s.get("cool_down") != null) p.put("coolDown", s.get("cool_down"));
                        if (s.get("precautions") != null) p.put("tips", s.get("precautions"));
                        p.put("title", str(p, "title", "我的专属训练方案"));
                    }
                } else if (modelOk) {
                    p.put("summary", truncate(realText(text), 220));
                }
                break;
            }
            case "weeklyReport": {
                // 真实 weekly 返回 {health_score, summary, highlights[], tips[], suggestions[]}
                if (modelOk && !s.isEmpty()) {
                    if (s.get("summary") != null) p.put("summary", s.get("summary"));
                    if (s.get("highlights") != null) p.put("highlights", s.get("highlights"));
                    if (s.get("tips") != null) p.put("issues", s.get("tips"));
                    if (s.get("suggestions") != null) p.put("suggestions", s.get("suggestions"));
                    if (s.get("health_score") != null) p.put("score", s.get("health_score"));
                    p.put("title", str(p, "title", "本周健康报告"));
                } else if (modelOk) {
                    p.put("summary", truncate(realText(text), 320));
                }
                break;
            }
            case "consult": {
                // 真实 chat 返回回答文本；question 来自 payload.question
                if (modelOk) {
                    String q = str(p, "question", "");
                    List<Map<String, String>> msgs = new ArrayList<>();
                    if (!q.trim().isEmpty()) msgs.add(mapOfStr("role", "user", "content", q));
                    msgs.add(mapOfStr("role", "ai", "content", realText(text)));
                    p.put("messages", msgs);
                    p.put("answer", realText(text));
                    p.put("advice", truncate(realText(text), 220));
                    p.put("summary", truncate(realText(text), 150));
                    p.put("disclaimer", "以上内容由 AI 生成，仅供健康科普参考，不构成医疗建议。");
                }
                break;
            }
            default:
                break;
        }
        if (!modelOk) {
            p.put("__modelError", aiError == null ? "生成内容为空" : aiError);
            p.put("__fallback", "大模型调用失败，以下为演示骨架内容，真实流水线步骤仍完整执行。");
        }
        return p;
    }

    private static String realText(String text) {
        return text == null ? "" : text.trim();
    }

    private static String firstNonEmpty(String... parts) {
        for (String part : parts) {
            if (part != null && !part.trim().isEmpty() && !"null".equalsIgnoreCase(part.trim())) return part;
        }
        return "";
    }

    private static String joinList(List<?> list, String sep) {
        if (list == null || list.isEmpty()) return "";
        StringBuilder sb = new StringBuilder();
        for (Object o : list) {
            String s = String.valueOf(o);
            if (s != null && !s.trim().isEmpty()) {
                if (sb.length() > 0) sb.append(sep);
                sb.append(s.trim());
            }
        }
        return sb.toString();
    }

    /** 从 map 中按英文/中文键依次取值，取到第一个非 null 的值。 */
    private static Object firstOf(Map<String, Object> plan, String... keys) {
        for (String key : keys) {
            Object v = plan.get(key);
            if (v != null) return v;
        }
        return null;
    }

    /** 把 AI 返回的三餐项归一化为字符串数组（{food, portion} → "食物 份量"）。 */
    private static List<Object> planMeals(Object v) {
        List<Object> out = new ArrayList<>();
        if (v instanceof List) {
            for (Object o : (List<?>) v) {
                if (o instanceof Map) {
                    Map<?, ?> m = (Map<?, ?>) o;
                    Object food = m.get("food") != null ? m.get("food") : m.get("name");
                    Object portion = m.get("portion") != null ? m.get("portion") : m.get("amount");
                    if (food != null) {
                        String s = String.valueOf(food).trim();
                        if (portion != null && !"null".equalsIgnoreCase(String.valueOf(portion).trim())) {
                            s += " " + String.valueOf(portion).trim();
                        }
                        out.add(s);
                    }
                } else if (o != null) {
                    out.add(String.valueOf(o));
                }
            }
        } else if (v != null) {
            out.add(String.valueOf(v));
        }
        return out;
    }

    private static List<Object> listOf(Object o) {
        return o instanceof List ? (List<Object>) o : new ArrayList<>();
    }

    private static Map<String, String> mapOfStr(Object... kvs) {
        Map<String, String> m = new LinkedHashMap<>();
        for (int i = 0; i + 1 < kvs.length; i += 2) m.put(String.valueOf(kvs[i]), String.valueOf(kvs[i + 1]));
        return m;
    }

    // ==================== 小工具 ====================

    private String aiEndpoint(String funcType) {
        switch (funcType) {
            case "article": return "POST /api/v1/articles/mother-draft";
            case "recipe": return "POST /api/v1/food/recommend";
            case "dietPlan": return "POST /api/v1/diet/plan";
            case "nutrition": return "POST /api/v1/nutrition/analyze";
            case "training": return "POST /api/v1/exercise/advice";
            case "weeklyReport": return "POST /api/v1/report/weekly-summary";
            default: return "POST /api/v1/chat";
        }
    }

    private Map<String, Object> requestBodyFor(String funcType, Object payload) {
        Map<String, Object> m = new LinkedHashMap<>();
        if (payload instanceof Map) {
            m.putAll((Map<String, Object>) payload);
        }
        return m;
    }

    private Map<String, Object> profileToAi(Map<String, Object> profile) {
        Map<String, Object> m = new LinkedHashMap<>();
        Object crowd = profile.get("crowdType");
        m.put("username", profile.get("username"));
        m.put("gender", profile.get("gender"));
        m.put("age", profile.get("age"));
        m.put("height", profile.get("height"));
        m.put("weight", profile.get("weight"));
        m.put("crowd_type", crowd == null ? "普通人" : crowd);
        m.put("taste_preference", profile.get("tastePreference"));
        m.put("allergic_foods", profile.get("allergicFoods"));
        m.put("dietary_restrictions", profile.get("dietaryRestrictions"));
        return m;
    }

    private String crowdOf(Map<String, Object> profile) {
        if (profile == null) return "普通人";
        Object c = profile.get("crowdType");
        return (c != null && !c.toString().trim().isEmpty()) ? c.toString() : "普通人";
    }

    /** 按功能类型提取真实查询主题：优先用户输入（描述/目标/问题/主题），避免用统一默认文案检索。 */
    private String topicOf(String funcType, Object payload) {
        if (payload instanceof Map) {
            Map<?, ?> m = (Map<?, ?>) payload;
            if ("article".equals(funcType)) {
                Object t = m.get("topic");
                if (t != null && !t.toString().trim().isEmpty()) return t.toString();
                return "健康科普";
            }
            if ("recipe".equals(funcType)) {
                Object d = m.get("description");
                if (d != null && !d.toString().trim().isEmpty()) return d.toString();
                Object g = m.get("goal");
                if (g != null && !g.toString().trim().isEmpty()) return g.toString();
                return "健康饮食与生活方式";
            }
            if ("dietPlan".equals(funcType) || "nutrition".equals(funcType) || "training".equals(funcType)) {
                Object g = m.get("goal");
                if (g != null && !g.toString().trim().isEmpty()) return g.toString();
                Object d = m.get("description");
                if (d != null && !d.toString().trim().isEmpty()) return d.toString();
                Object p = m.get("preferences");
                if (p != null && !p.toString().trim().isEmpty()) return p.toString();
                return "健康饮食与生活方式";
            }
            if ("consult".equals(funcType)) {
                Object q = m.get("question");
                if (q != null && !q.toString().trim().isEmpty()) return q.toString();
                return "健康咨询";
            }
            if ("weeklyReport".equals(funcType)) {
                Object s = m.get("summary");
                if (s != null && !s.toString().trim().isEmpty()) return s.toString();
                return "本周健康周报";
            }
        }
        return "健康饮食与生活方式";
    }

    private String questionOf(Object payload) {
        if (payload instanceof Map) {
            Object q = ((Map<?, ?>) payload).get("question");
            if (q != null && !q.toString().trim().isEmpty()) return q.toString();
        }
        return "请结合我的情况，给出专业、可执行、分条的健康建议。";
    }

    private String titleOf(Map<String, Object> p, String fallback) {
        Object t = p.get("title");
        if (t != null && !t.toString().trim().isEmpty()) return t.toString();
        return fallback == null ? "AI 生成内容" : fallback;
    }

    private String summaryOf(Map<String, Object> p, String fallback) {
        Object s = p.get("summary");
        if (s != null && !s.toString().trim().isEmpty()) return s.toString();
        return fallback;
    }

    private static String truncate(Object o, int max) {
        if (o == null) return "";
        String s = o.toString().replace("\r", " ").replace("\n", " ");
        return s.length() <= max ? s : s.substring(0, max) + "…";
    }

    private static Map<String, Object> mapOf(Object... kvs) {
        Map<String, Object> m = new LinkedHashMap<>();
        for (int i = 0; i + 1 < kvs.length; i += 2) m.put(String.valueOf(kvs[i]), kvs[i + 1]);
        return m;
    }

    private static List<String> sampleKeys(Object payload, int n) {
        List<String> out = new ArrayList<>();
        if (payload instanceof Map) {
            for (Object k : ((Map<?, ?>) payload).keySet()) {
                out.add(String.valueOf(k));
                if (out.size() >= n) break;
            }
        }
        return out;
    }

    private static String str(Object o, String k, String fallback) {
        if (o instanceof Map) {
            Object v = ((Map<?, ?>) o).get(k);
            if (v != null && !v.toString().trim().isEmpty()) return v.toString();
        }
        return fallback;
    }

    private static List<String> firstList(Object payload, String key, List<String> fallback) {
        if (payload instanceof Map) {
            Object v = ((Map<?, ?>) payload).get(key);
            if (v instanceof List) {
                List<String> out = new ArrayList<>();
                for (Object item : (List<?>) v) {
                    if (item != null && !item.toString().trim().isEmpty()) out.add(item.toString());
                }
                if (!out.isEmpty()) return out;
            }
        }
        return fallback;
    }

    private static final class Generation {
        final String text;
        final String error;
        final Map<String, Object> tokens;
        final Map<String, Object> structured; // 结构化结果（食谱/膳食/运动/营养/周报的 data.response dict）
        final Map<String, Object> meta;       // _meta（mode/route/trace）
        Generation(String text, String error) {
            this(text, error, null, null, null);
        }
        Generation(String text, String error, Map<String, Object> tokens) {
            this(text, error, tokens, null, null);
        }
        Generation(String text, String error, Map<String, Object> tokens,
                   Map<String, Object> structured, Map<String, Object> meta) {
            this.text = text == null ? "" : text;
            this.error = error;
            this.tokens = tokens;
            this.structured = structured;
            this.meta = meta;
        }
    }
}
