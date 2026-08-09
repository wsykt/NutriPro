"""Agent 统一编排调度器

集中管理：
1. Agent 路由分发（自动匹配最合适的 Agent 处理请求）
2. 上下文组装（用户资料 + 记忆 + 知识库）
3. 缓存读取/写入
4. 超时控制 + 降级（LLM 失败切本地兜底）
5. 运行统计埋点

所有 API 接口统一通过 Orchestrator 调用，不再硬编码调用具体 Agent。
"""

import time
import json
import os
import re
import logging
from typing import Optional, Dict, Any, Callable, Tuple, List
from config.settings import settings
from utils.cache_utils import cache_agent_result, get_cached_agent_result
from services.disclaimer import STANDARD_DISCLAIMER

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Agent 编排器"""

    def __init__(self):
        self._agents = {}
        self._fallback_handlers = {}  # agent_name -> fallback handler
        self._local_engine = None
        self._retriever = None
        self._store = None
        self._llm = None
        self._memory_extractor = None
        self._mode_router = None  # 新增：A/C方案模式路由器
        self._validator = None    # 新增：三组件校验流水线（事实/数值/安全）
        self._stats = {}  # agent_name -> {"calls": 0, "success": 0, "total_time": 0, "llm_fails": 0, "fallbacks": 0}
        self._detailed_logs = []  # 详细调用日志（用于导出）
        self._max_detailed_logs = 1000

    def init(self, llm, retriever, store, memory_extractor, local_engine):
        """注入依赖"""
        self._llm = llm
        self._retriever = retriever
        self._store = store
        self._memory_extractor = memory_extractor
        self._local_engine = local_engine
        # 初始化 A/C 方案模式路由器
        from services.mode_router import mode_router
        from config.settings import settings
        mode_router.init(
            llm=llm, retriever=retriever, local_engine=local_engine,
            auto_ingest=settings.KB_AUTO_INGEST_C_RESULTS,
        )
        # 同步覆盖相似度阈值（如果用户在 env 里调了）
        if hasattr(settings, "KB_DUP_SIMILARITY_THRESHOLD") and settings.KB_DUP_SIMILARITY_THRESHOLD > 0:
            mode_router.DUP_SIMILARITY_THRESHOLD = settings.KB_DUP_SIMILARITY_THRESHOLD
        self._mode_router = mode_router

        # 初始化三组件校验流水线（事实校验/数值检查/安全拦截）
        try:
            from agent.validators.validator import ValidatorPipeline
            self._validator = ValidatorPipeline(enabled=settings.VALIDATOR_ENABLED)
            logger.info(f"[orchestrator] 校验流水线已启用 enabled={settings.VALIDATOR_ENABLED}")
        except Exception as e:
            logger.warning(f"[orchestrator] 校验流水线初始化失败，降级跳过校验: {e}")
            self._validator = None

        self._register_agents()
        self._register_fallback_handlers()

    def _register_agents(self):
        """注册所有 Agent（整合方法映射）"""
        from agent.retrieve_judge import agent as judge
        from agent.voice_text_parse import agent as voice
        from agent.nutrition_analysis import agent as nutrition
        from agent.food_audit import agent as food_audit
        from agent.diet_plan import agent as diet
        from agent.weekly_report import agent as weekly
        from agent.article_generate import agent as article
        from agent.health_reflection import agent as reflect
        from agent.food_recommend import agent as food_rec
        from agent.exercise_advice import agent as exercise
        from agent.nlu_parser import agent as nlu_parser

        # 方法映射：每个 Agent 有自己独立的调用方法签名
        self._agents = {
            "judge": lambda q: judge.judge(q),
            "voice": lambda text=None: voice.parse(text) if text else {"items": []},
            "nutrition": lambda up, dn, de: nutrition.analyze(up, dn, de),
            "food_audit": lambda fd: food_audit.audit(fd),
            "diet": lambda up, g: diet.generate(up, g),
            "weekly": lambda up, ws: weekly.generate(up, ws),
            "article": lambda tp, tc: article.generate(tp, tc),
            "reflect": lambda q, r, rating, reason: reflect.reflect(q, r, rating, reason),
            "reflect_health": lambda up, hd, c: reflect.health_reflection(up, hd, c),
            "food_recommend": lambda ings, ct, g: food_rec.recommend(ings, ct, g),
            "exercise": lambda up, g, pref, cd: exercise.advise(up, g, pref, cd),
            "nlu_parse": lambda text, meal_type=None: nlu_parser.parse_meal(text, meal_type) if meal_type else nlu_parser.parse(text),
        }

    def _register_fallback_handlers(self):
        """注册所有 Agent 的兜底处理器（注册表模式，符合开闭原则）"""
        LE = self._local_engine
        if not LE:
            return

        self._fallback_handlers = {
            "diet": lambda args, kw: LE.fallback_diet_plan(
                args[0] if args else kw.get("user_profile", {}),
                args[1] if len(args) > 1 else kw.get("goal", "")),
            "weekly": lambda args, kw: LE.fallback_weekly_report(
                args[0] if args else kw.get("user_profile", {}),
                args[1] if len(args) > 1 else kw.get("weekly_stats", {})),
            "food_audit": lambda args, kw: LE.fallback_food_audit(
                args[0] if args else kw),
            "voice": lambda args, kw: LE.fallback_voice_parse(
                args[0] if args else kw.get("text", "")),
            "nutrition": lambda args, kw: LE.fallback_nutrition_analysis(
                args[0] if args else kw.get("user_profile", {}),
                args[1] if len(args) > 1 else kw.get("daily_nutrition", {}),
                args[2] if len(args) > 2 else kw.get("daily_exercise", {})),
            "article": lambda args, kw: LE.fallback_article_generate(
                args[0] if args else kw.get("topic", ""),
                args[1] if len(args) > 1 else kw.get("target_crowd", "")),
            "food_recommend": lambda args, kw: LE.fallback_food_recommend(
                args[0] if args else kw.get("ingredients", []),
                args[1] if len(args) > 1 else kw.get("crowd_type", "普通人"),
                args[2] if len(args) > 2 else kw.get("goal", "健康饮食")),
            "exercise": lambda args, kw: LE.fallback_exercise_advice(
                args[0] if args else kw.get("user_profile", {}),
                args[1] if len(args) > 1 else kw.get("goal", "保持健康"),
                args[2] if len(args) > 2 else kw.get("preferences", ""),
                args[3] if len(args) > 3 else kw.get("chronic_diseases", [])),
            "reflect": lambda args, kw: {
                "issue_type": "other",
                "analysis": "AI服务暂不可用，无法进行回答质量分析",
                "suggested_action": "等待AI服务恢复后重新分析",
                "fallback": True, "template_type": "reflect_fallback"},
            "reflect_health": lambda args, kw: LE.fallback_health_reflection(
                args[0] if args else kw.get("user_profile", {}),
                args[1] if len(args) > 1 else kw.get("health_data", {}),
                args[2] if len(args) > 2 else kw.get("concerns", [])),
            "nlu_parse": lambda args, kw: {
                "error": "AI服务暂不可用，无法解析饮食描述",
                "fallback": True},
        }

    def _record_stat(self, agent_name: str, success: bool, elapsed: float,
                     is_llm_fail: bool = False, is_fallback: bool = False):
        """记录运行统计"""
        if agent_name not in self._stats:
            self._stats[agent_name] = {"calls": 0, "success": 0, "total_time": 0, "llm_fails": 0, "fallbacks": 0}
        self._stats[agent_name]["calls"] += 1
        self._stats[agent_name]["total_time"] += elapsed
        if success:
            self._stats[agent_name]["success"] += 1
        if is_llm_fail:
            self._stats[agent_name]["llm_fails"] = self._stats[agent_name].get("llm_fails", 0) + 1
        if is_fallback:
            self._stats[agent_name]["fallbacks"] = self._stats[agent_name].get("fallbacks", 0) + 1

        # 详细日志
        if len(self._detailed_logs) < self._max_detailed_logs:
            self._detailed_logs.append({
                "agent": agent_name,
                "success": success,
                "elapsed_ms": round(elapsed * 1000, 1),
                "is_llm_fail": is_llm_fail,
                "is_fallback": is_fallback,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            })

    def get_stats(self) -> dict:
        """获取所有 Agent 运行统计"""
        result = {}
        for name, data in self._stats.items():
            result[name] = {
                "calls": data["calls"],
                "success_rate": round(data["success"] / max(data["calls"], 1) * 100, 1),
                "avg_time_ms": round(data["total_time"] / max(data["calls"], 1) * 1000, 1),
                "llm_fails": data.get("llm_fails", 0),
                "fallbacks": data.get("fallbacks", 0),
            }
        return result

    def get_full_stats(self) -> list:
        """获取完整调用日志（用于导出）"""
        return list(self._detailed_logs)

    def _build_context(self, user_id: int, health_snapshot: dict = None) -> str:
        """组装上下文：用户记忆 + 今日快照"""
        context_parts = []

        # 1. 长期记忆
        if self._memory_extractor and user_id > 0:
            memory_text = self._memory_extractor.to_context_string(user_id)
            if memory_text:
                context_parts.append(memory_text)

        # 2. 今日快照
        if health_snapshot:
            profile = health_snapshot.get("profile", {})
            user_info = []
            if profile.get("username"):
                user_info.append(f"姓名：{profile['username']}")
            if profile.get("gender"):
                user_info.append(f"性别：{profile['gender']}")
            if profile.get("age"):
                user_info.append(f"年龄：{profile['age']}")
            if profile.get("height_cm"):
                user_info.append(f"身高：{profile['height_cm']}cm")
            if profile.get("weight_kg"):
                user_info.append(f"体重：{profile['weight_kg']}kg")
            if profile.get("bmi"):
                user_info.append(f"BMI：{profile['bmi']}")
            if profile.get("crowdType"):
                user_info.append(f"人群标签：{profile['crowdType']}")

            if user_info:
                context_parts.append("【今日健康数据】\n" + "\n".join(user_info))

        return "\n\n".join(context_parts)

    def _get_knowledge_context(self, query: str, target_crowd: str = "") -> Tuple[str, List[dict]]:
        """检索知识库并组装上下文

        返回: (context_str, raw_results)
        """
        if not self._retriever or self._retriever.count() == 0:
            return "", []

        try:
            from agent.retrieve_judge import agent as judge
            judge_result = judge.judge(query)

            if not judge_result.get("need_retrieve"):
                return "", []

            # 使用动态 top_k 混合检索（按相似度分布分段取条数，降低 prompt 冗余）
            kb_results = self._retriever.dynamic_retrieve(
                query,
                target_crowd=target_crowd if judge_result.get("need_retrieve") else None,
                default_top_k=5,
            )

            if kb_results:
                context = "\n---知识库参考---\n"
                for r in kb_results:
                    source = r.get("metadata", {}).get("source", "")
                    tag = " [权威]" if r.get("is_authority") else ""
                    context += f"- {r['content']}{tag}\n"
                return context, kb_results
        except Exception:
            pass

        return "", []

    # ============================================================
    # 公开调度方法
    # ============================================================

    def chat(self, user_id: int, message: str, health_snapshot: dict = None,
             conversation_id: str = "", force_fallback: bool = False,
             high_performance: bool = False) -> dict:
        """聊天对话调度 — 支持双模式：

        - high_performance=true:  高性能模式，直接 C 方案云端生成，跳过本地校验（演示用，速度快）
        - high_performance=false: 正常模式，模板召回→本地改写(A)→校验失败回退 C 方案
        """
        start = time.time()

        # Pipeline Stage 1: 记忆提取
        self._stage_extract_memory(user_id, message)

        # Pipeline Stage 2: 上下文组装
        context = self._build_context(user_id, health_snapshot)
        target_crowd = (health_snapshot or {}).get("profile", {}).get("crowdType", "")
        user_profile = (health_snapshot or {}).get("profile", {}) or {}

        # Pipeline Stage 3: 知识库检索
        retrieval_start = time.time()
        kb_context, kb_raw_results = self._get_knowledge_context(message, target_crowd)
        retrieval_time_ms = round((time.time() - retrieval_start) * 1000)

        retrieve_info = self._build_retrieve_info(kb_raw_results)

        # Pipeline Stage 4: NLU 饮食解析
        nlu_context = self._stage_nlu_parse(message)

        # Pipeline Stage 5: 对话管理
        conversation_id = self._stage_conversation(user_id, message, conversation_id, health_snapshot)
        context_messages = self._store.get_context(conversation_id, max_messages=6)

        # ========== 双模式分流 ==========
        chronic_diseases = user_profile.get("chronic_diseases", []) if isinstance(user_profile, dict) else []

        if not force_fallback and self._mode_router:
            # --- 使用 ModeRouter 双模式调度 ---
            router_params = dict(
                func_type="qa",
                high_performance=high_performance,
                question=message,
                user_profile=user_profile,
                health_snapshot=health_snapshot or {},
                chronic_diseases=chronic_diseases,
            )
            # 把历史上下文也塞进 prompt（拼接进 question 上下文）
            if context_messages:
                hist = "\n".join(
                    f"{'用户' if m['role']=='user' else '助手'}: {m['content']}"
                    for m in context_messages[-4:]
                )
                router_params["question"] = f"[历史对话]\n{hist}\n\n[当前问题]\n{message}"

            router_start = time.time()
            router_result = self._mode_router.route(**router_params)
            response = router_result.get("result", "")
            route = router_result.get("route", "")
            mode = router_result.get("mode", "")
            router_timing = router_result.get("timing_ms", {})

            # provider 判定
            if mode == "high_performance" or route == "C_direct" or route == "C_fallback":
                provider = "deepseek"
            else:
                provider = "local_fallback" if route == "A_template_local" else "deepseek"

            llm_time_ms = router_timing.get("cloud_ms", 0) + router_timing.get("local_rewrite_ms", 0)
            total_ms = round((time.time() - start) * 1000)
            validation_ms = router_timing.get("validate_a_ms", 0) + router_timing.get("validate_c_ms", 0)

            # 后处理 + 存储
            response = self._stage_post_process(str(response), provider)
            # qa 安全拦截（高风险内容替换为安全响应）
            response = self._guard_qa_response(response, target_crowd=user_profile.get("crowd_type", "") if isinstance(user_profile, dict) else "", chronic=chronic_diseases)
            self._store.add_message(conversation_id, "assistant", response)
            self._record_stat("chat", provider == "deepseek", time.time() - start)

            timing_breakdown = {
                "retrieval_ms": retrieval_time_ms,
                "llm_ms": llm_time_ms,
                "validation_ms": validation_ms,
                "router_ms": round((time.time() - router_start) * 1000),
                "total_ms": total_ms,
            }
            timing_breakdown.update(router_timing)

            return {
                "conversation_id": conversation_id,
                "response": response,
                "provider": provider,
                "mode": mode,
                "route": route,
                "high_performance": high_performance,
                "validation": router_result.get("validation", {}),
                "elapsed_seconds": round((time.time() - start), 2),
                "retrieve_info": retrieve_info,
                "timing_breakdown": timing_breakdown,
            }

        # --- 原有流水线（force_fallback 或 mode_router 未初始化时走这里）---
        # Pipeline Stage 6: Prompt 组装 + LLM 调用
        messages = self._build_messages(context, kb_context, nlu_context, context_messages, message)
        response, provider, llm_time_ms = self._stage_llm_call(messages, message, health_snapshot, force_fallback)

        # Pipeline Stage 7: 后处理（免责声明 + 存储）
        response = self._stage_post_process(response, provider)
        # qa 安全拦截（高风险内容替换为安全响应）
        response = self._guard_qa_response(response, target_crowd=user_profile.get("crowd_type", "") if isinstance(user_profile, dict) else "", chronic=chronic_diseases)
        self._store.add_message(conversation_id, "assistant", response)

        elapsed = time.time() - start
        total_ms = round(elapsed * 1000)
        validation_ms = max(0, total_ms - retrieval_time_ms - llm_time_ms)
        self._record_stat("chat", provider == "deepseek", elapsed)

        return {
            "conversation_id": conversation_id,
            "response": response,
            "provider": provider,
            "mode": "legacy" if high_performance else "normal_legacy",
            "route": "legacy_pipeline",
            "high_performance": high_performance,
            "elapsed_seconds": round(elapsed, 2),
            "retrieve_info": retrieve_info,
            "timing_breakdown": {
                "retrieval_ms": retrieval_time_ms,
                "llm_ms": llm_time_ms,
                "validation_ms": validation_ms,
                "total_ms": total_ms,
            },
        }

    # --- Pipeline 阶段方法 ---

    def chat_stream_setup(self, user_id: int, message: str, health_snapshot: dict = None,
                          conversation_id: str = "", high_performance: bool = False):
        """SSE 真流式前置准备（高性能模式专用）

        与 chat() 保持一致的状态流转（记忆提取/对话管理/历史上下文），
        但把 LLM 调用替换为云端流式生成（mode_router.stream_qa）。

        返回: (conversation_id, stream_gen)；
        非高性能模式或 mode_router 未初始化时返回 None（调用方回退完整链路）。
        """
        if not high_performance or not self._mode_router:
            return None

        # Stage 1: 记忆提取
        self._stage_extract_memory(user_id, message)

        # Stage 5: 对话管理
        conversation_id = self._stage_conversation(user_id, message, conversation_id, health_snapshot)
        context_messages = self._store.get_context(conversation_id, max_messages=6)

        user_profile = (health_snapshot or {}).get("profile", {}) or {}
        chronic_diseases = user_profile.get("chronic_diseases", []) if isinstance(user_profile, dict) else []
        router_kwargs = dict(
            func_type="qa",
            high_performance=True,
            question=message,
            user_profile=user_profile,
            health_snapshot=health_snapshot or {},
            chronic_diseases=chronic_diseases,
        )
        # 历史上下文拼进 question（与 chat() 高性能分支一致）
        if context_messages:
            hist = "\n".join(
                f"{'用户' if m['role']=='user' else '助手'}: {m['content']}"
                for m in context_messages[-4:]
            )
            router_kwargs["question"] = f"[历史对话]\n{hist}\n\n[当前问题]\n{message}"

        stream_gen = self._mode_router.stream_qa(**router_kwargs)
        return conversation_id, stream_gen

    def finalize_chat_stream(self, conversation_id: str, full_text: str,
                             health_snapshot: dict = None) -> str:
        """SSE 真流式收尾：后处理（免责声明去重/安全拦截）+ 写入对话记录

        与 chat() 的后处理保持一致，返回最终文本（供 done 事件回传）。
        """
        provider = "deepseek"
        text = self._stage_post_process(str(full_text), provider)
        user_profile = (health_snapshot or {}).get("profile", {}) or {}
        text = self._guard_qa_response(
            text,
            target_crowd=user_profile.get("crowd_type", "") if isinstance(user_profile, dict) else "",
            chronic=user_profile.get("chronic_diseases", []) if isinstance(user_profile, dict) else [],
        )
        if conversation_id:
            self._store.add_message(conversation_id, "assistant", text)
        return text


    def _stage_extract_memory(self, user_id: int, message: str):
        """Stage 1: 提取长期记忆"""
        if user_id > 0 and self._memory_extractor:
            self._memory_extractor.extract_from_dialogue(user_id, [
                {"role": "user", "content": message}
            ])

    def _stage_nlu_parse(self, message: str) -> str:
        """Stage 4: NLU 饮食解析（检测到饮食相关内容时自动触发）"""
        diet_keywords = ["吃了", "早餐", "午餐", "晚餐", "加餐", "喝了", "个", "碗", "杯", "g", "克"]
        if not any(kw in message for kw in diet_keywords):
            return ""
        try:
            from agent.nlu_parser import NLUParser
            nlu_result = NLUParser.parse(message)
            if not nlu_result.get("meals") or not any(m.get("foods") for m in nlu_result.get("meals", {}).values() if m):
                return ""
            daily_totals = nlu_result.get("daily_totals", {})
            nlu_context = "\n---饮食解析结果（自动识别）---\n"
            for meal_type, meal_data in nlu_result.get("meals", {}).items():
                foods_str = "、".join(
                    f"{f['food_name_matched']}({f['amount_description']})"
                    for f in meal_data.get("foods", [])
                )
                if foods_str:
                    nlu_context += f"{meal_type}: {foods_str}\n"
            if daily_totals:
                nlu_context += f"总计热量: {daily_totals.get('calorie', 0)}kcal | "
                nlu_context += f"蛋白质: {daily_totals.get('protein', 0)}g | "
                nlu_context += f"碳水: {daily_totals.get('carb', 0)}g | "
                nlu_context += f"脂肪: {daily_totals.get('fat', 0)}g\n"
            return nlu_context
        except Exception:
            return ""

    def _stage_conversation(self, user_id: int, message: str, conversation_id: str, health_snapshot: dict) -> str:
        """Stage 5: 对话管理"""
        if not conversation_id:
            conversation_id = self._store.create_conversation(user_id)
        else:
            self._store.create_conversation(user_id, conversation_id)
        self._store.add_message(conversation_id, "user", message,
                                json.dumps(health_snapshot, ensure_ascii=False))
        return conversation_id

    def _build_messages(self, context: str, kb_context: str, nlu_context: str,
                        context_messages: list, message: str) -> list:
        """Stage 6a: 构建 Prompt"""
        system_prompt = "你是一个专业的健康咨询助手，用中文给出实用的健康建议。\n\n"
        if context:
            system_prompt += f"{context}\n\n"
        if kb_context:
            system_prompt += f"{kb_context}\n\n"
        if nlu_context:
            system_prompt += f"{nlu_context}\n\n"
        system_prompt += "输出要求：\n1. 基于上述数据给出具体建议\n2. 不提供疾病诊断，仅膳食科普\n3. 用中文回答，条理清晰"

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(context_messages)
        messages.append({"role": "user", "content": message})
        return messages

    def _stage_llm_call(self, messages: list, message: str, health_snapshot: dict, force_fallback: bool) -> Tuple[str, str, int]:
        """Stage 6b: LLM 调用（带降级）"""
        provider = "deepseek"
        force_fallback = force_fallback or os.environ.get("FORCE_FALLBACK", "").lower() in ("true", "1", "yes")
        llm_start = time.time()
        try:
            if force_fallback:
                raise Exception("FORCE_FALLBACK enabled - simulating LLM failure")
            if self._llm:
                response = self._llm.chat(messages)
            else:
                raise ValueError("LLM not initialized")
            llm_time_ms = round((time.time() - llm_start) * 1000)
        except Exception as e:
            llm_time_ms = round((time.time() - llm_start) * 1000)
            provider = "local_fallback"
            error_msg = str(e).lower()
            if "timeout" in error_msg:
                response = "⚠️ AI 服务响应超时，已切换至本地知识库回答。\n\n"
            elif "auth" in error_msg or "key" in error_msg:
                response = "⚠️ AI 服务认证失败，已切换至本地知识库回答。\n\n"
            elif "rate" in error_msg or "limit" in error_msg:
                response = "⚠️ AI 服务繁忙，已切换至本地知识库回答。\n\n"
            else:
                response = "⚠️ AI 服务暂时不可用，已切换至本地知识库回答。\n\n"
            if self._local_engine:
                response += self._local_engine.answer_health_query(message, health_snapshot)
            else:
                response += "请稍后重试。"
        return response, provider, llm_time_ms

    def _stage_post_process(self, response: str, provider: str) -> str:
        """Stage 7: 后处理（免责声明去重 + 统一添加）"""
        response = re.sub(
            r'\n*[*]*[免责声明|温馨提示|Disclaimer][：:][^\n]*(?:不构成医疗建议|仅供参考|慢性病请遵从)[^\n]*\n*',
            '', response, flags=re.IGNORECASE
        )
        response = re.sub(r'\n{3,}', '\n\n', response).strip()
        if provider == "deepseek" and STANDARD_DISCLAIMER not in response:
            response += "\n\n" + STANDARD_DISCLAIMER
        return response

    def _build_retrieve_info(self, kb_raw_results: list) -> list:
        """构建检索信息（用于前端展示）"""
        if not kb_raw_results:
            return None
        retrieve_info = []
        for r in kb_raw_results:
            retrieve_info.append({
                "content": r.get("content", "")[:200],
                "similarity": round(r.get("similarity", 0), 4),
                "source": r.get("metadata", {}).get("source", ""),
                "category": r.get("metadata", {}).get("category", ""),
            })
        return retrieve_info

    def _build_cache_key(self, agent_name: str, args: tuple, kwargs: dict) -> str:
        """构建缓存键（支持 dict/list 等复杂类型）"""
        cache_key_parts = [agent_name]
        for arg in args:
            if isinstance(arg, (str, int, float)):
                cache_key_parts.append(str(arg))
            elif isinstance(arg, (dict, list, tuple)):
                cache_key_parts.append(json.dumps(arg, sort_keys=True, ensure_ascii=False))
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float)):
                cache_key_parts.append(f"{k}={v}")
            elif isinstance(v, (dict, list, tuple)):
                cache_key_parts.append(f"{k}={json.dumps(v, sort_keys=True, ensure_ascii=False)}")
        return str(hash("|".join(cache_key_parts)))

    def process(self, agent_name: str, *args, **kwargs) -> Any:
        """通用 Agent 调用入口（含缓存 + 统计 + 降级 + A/C双模式调度）

        新增支持：从 kwargs 中提取 high_performance 参数，走 ModeRouter 双模式：
          - True:  高性能模式，直接 C 方案云端生成，跳过校验（演示用快）
          - False: 正常模式，模板召回→本地改写(A)→失败回退C方案

        支持的 agent_name（4个结构化功能）：
          - diet           → func_type: diet_plan
          - food_recommend → func_type: food_recommend
          - exercise       → func_type: exercise
          - nutrition      → 保留原有 Agent（无ModeRouter，走旧逻辑）
        """
        start = time.time()

        # 提取 high_performance 开关（不参与缓存键，避免相同输入不同模式都查缓存）
        high_performance = bool(kwargs.pop("high_performance", False))

        # 缓存键提取（支持 dict/list 等复杂类型）
        params_hash = self._build_cache_key(agent_name, args, kwargs)

        # 读缓存
        user_id = kwargs.get("user_id", 0) or (args[0] if args and isinstance(args[0], int) else 0)
        cached = get_cached_agent_result(agent_name, user_id, params_hash)
        if cached is not None and not high_performance:
            # 高性能模式不读缓存，保证速度演示新鲜结果
            return cached

        # ============== 4 个结构化功能走 ModeRouter 双模式 ==============
        ROUTER_MAP = {
            "diet":           "diet_plan",
            "food_recommend": "food_recommend",
            "exercise":       "exercise",
        }
        func_type = ROUTER_MAP.get(agent_name)

        if func_type and self._mode_router and not kwargs.get("_force_old_pipeline", False):
            # --- 参数解包 & 路由分发 ---
            router_kwargs = self._extract_router_kwargs(agent_name, args, kwargs)
            router_kwargs["func_type"] = func_type
            router_kwargs["high_performance"] = high_performance

            router_start = time.time()
            try:
                router_result = self._mode_router.route(**router_kwargs)
                result = router_result.get("result")
                route = router_result.get("route", "")
                mode = router_result.get("mode", "")
                success = True
                is_llm_fail = False
                is_fallback = route == "C_fallback" or route == "A_template_local" and not router_result.get("validation", {}).get("passed", True)

                # 包装 result，注入模式元信息（前端可展示但不影响数据）
                if isinstance(result, dict):
                    result["_meta"] = {
                        "high_performance": high_performance,
                        "mode": mode,
                        "route": route,
                        "timing_ms": router_result.get("timing_ms", {}),
                        "validation": router_result.get("validation", {}),
                    }
                elapsed = time.time() - start
                self._record_stat(agent_name, success, elapsed, is_llm_fail, is_fallback)

                # 三组件校验（安全拦截→数值检查→事实校验）；BLOCK 时替换为安全响应
                result = self._validate_and_guard(agent_name, func_type, result,
                                                  high_performance, router_result, kwargs)

                # 写缓存（正常模式读缓存；高性能模式也写，供后续正常模式复用，保证演示新鲜结果）
                if success:
                    cache_agent_result(agent_name, user_id, params_hash, result)

                return result
            except Exception as e:
                # Router 执行失败，走旧逻辑兜底
                pass

        # ============== 原有流水线（其他 Agent / Router 失败时回退） ==============
        agent = self._agents.get(agent_name)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_name}")

        try:
            result = agent(*args, **kwargs)
            success = True
            is_llm_fail = False
            is_fallback = False
        except Exception as e:
            # 降级：尝试本地引擎
            success = False
            is_llm_fail = True
            is_fallback = True
            if self._local_engine:
                result = self._unified_fallback(agent_name, kwargs, args)
            else:
                raise e

        elapsed = time.time() - start
        self._record_stat(agent_name, success, elapsed, is_llm_fail, is_fallback)

        # 三组件校验（qa 文本类结果走安全拦截+数值+事实；其他 agent 仅安全拦截）
        result = self._validate_and_guard(agent_name, func_type, result,
                                          high_performance, None, kwargs)

        # 写缓存（正常模式读缓存；高性能模式也写，供后续正常模式复用）
        if success:
            cache_agent_result(agent_name, user_id, params_hash, result)

        return result

    # ---------- 三组件校验（安全拦截→数值检查→事实校验） ----------
    def _validate_and_guard(self, agent_name: str, func_type: Optional[str],
                            result: Any, high_performance: bool,
                            router_result: Optional[dict], kwargs: dict) -> Any:
        """在返回结果前执行校验流水线：
        - 安全风险 BLOCK → 替换为安全响应
        - 数值/事实问题 → 附加到 _meta.validation（不阻断）
        - 仅对 4 个健康功能做完整校验；其他 agent 只做安全拦截
        """
        if not self._validator:
            return result
        # 需要人群/慢病信息
        target_crowd, chronic = self._extract_validation_context(agent_name, kwargs)

        # 判断是否为核心健康功能
        func = func_type or ("qa" if agent_name in ("judge", "chat", "qa") else agent_name)
        if func not in ("qa", "diet_plan", "food_recommend", "exercise"):
            # 其他 agent 仅安全拦截
            try:
                safety = self._validator.safety.check_json(result, target_crowd, chronic)
                if safety.get("level") == "block" and settings.VALIDATOR_BLOCK_SAFETY:
                    logger.warning(f"[校验-安全拦截] agent={agent_name} 检测到高风险内容，已替换响应")
                    return self._validator.safety.build_safe_response("qa", result, safety.get("issues", []))
            except Exception as e:
                logger.debug(f"[校验异常] {e}")
            return result

        # 核心功能：完整校验链
        kb_context = ""
        try:
            if self._retriever and kwargs.get("question") or kwargs.get("goal"):
                q = kwargs.get("question") or kwargs.get("goal") or ""
                hits = self._retriever.search(q, top_k=3, target_crowd=target_crowd or None)
                kb_context = "\n".join(h.get("content", "") for h in (hits or []))[:800]
        except Exception:
            pass

        try:
            v = self._validator.validate(func, result, target_crowd, chronic, kb_context)
        except Exception as e:
            logger.debug(f"[校验流水线异常] {e}")
            return result

        # BLOCK → 替换为安全响应
        if v.get("blocked") and settings.VALIDATOR_BLOCK_SAFETY:
            logger.warning(f"[校验-拦截] {agent_name} 高风险内容已替换响应 | issues={len(v.get('issues', []))}")
            return self._validator.safety.build_safe_response(func, result, v.get("issues", []))

        # 非阻断 → 附加校验信息到 _meta
        if isinstance(result, dict):
            if "_meta" not in result:
                result["_meta"] = {}
            result["_meta"]["validation"] = {
                **(result["_meta"].get("validation", {}) if isinstance(result["_meta"].get("validation"), dict) else {}),
                "validator": {
                    "level": v.get("level"),
                    "passed": v.get("passed"),
                    "safety": {"level": v.get("safety", {}).get("level")},
                    "numeric": {"severity": v.get("numeric", {}).get("severity")},
                    "fact": {"severity": v.get("fact", {}).get("severity")},
                    "issues": [i.get("message", "") for i in v.get("issues", [])][:5],
                },
            }
        return result

    def _extract_validation_context(self, agent_name: str, kwargs: dict) -> tuple:
        """从 kwargs 提取人群与慢病信息（用于校验）"""
        user_profile = kwargs.get("user_profile") or {}
        if not isinstance(user_profile, dict):
            user_profile = {}
        crowd = user_profile.get("crowd_type") or user_profile.get("crowdType") or ""
        if not crowd:
            crowd = kwargs.get("crowd_type", "") or kwargs.get("target_crowd", "")
        chronic = kwargs.get("chronic_diseases") or user_profile.get("chronic_diseases") or []
        if isinstance(chronic, str):
            chronic = [chronic]
        return crowd, chronic

    def _guard_qa_response(self, response: str, target_crowd: str = "",
                           chronic: list = None) -> str:
        """qa 文本结果安全拦截：检测到高风险内容时替换为安全响应（不阻断正常回答）"""
        if not self._validator or not response or not isinstance(response, str):
            return response
        try:
            safety = self._validator.safety.check(response, target_crowd, chronic or [])
            if safety.get("level") == "block" and settings.VALIDATOR_BLOCK_SAFETY:
                logger.warning(f"[校验-安全拦截] qa 检测到高风险内容，已替换响应")
                return self._validator.safety.build_safe_response("qa", response, safety.get("issues", []))
        except Exception as e:
            logger.debug(f"[qa安全拦截异常] {e}")
        return response

    # ---------- ModeRouter 参数解包（从 args/kwargs 还原为命名参数） ----------
    def _extract_router_kwargs(self, agent_name: str, args: tuple, kwargs: dict) -> dict:
        """把 orchestrator.process 的位置参数按 agent 映射成 ModeRouter 需要的命名参数"""
        rk = {}
        if agent_name == "diet":
            # diet: lambda up, g: diet.generate(up, g)
            rk["user_profile"] = args[0] if len(args) > 0 else kwargs.get("user_profile", {})
            rk["goal"] = args[1] if len(args) > 1 else kwargs.get("goal", "")
        elif agent_name == "food_recommend":
            # food_recommend: lambda ings, ct, g: food_rec.recommend(ings, ct, g)
            rk["ingredients"] = args[0] if len(args) > 0 else kwargs.get("ingredients", [])
            rk["crowd_type"] = args[1] if len(args) > 1 else kwargs.get("crowd_type", "普通人")
            rk["goal"] = args[2] if len(args) > 2 else kwargs.get("goal", "健康饮食")
            if kwargs.get("user_profile"):
                rk["user_profile"] = kwargs["user_profile"]
        elif agent_name == "exercise":
            # exercise: lambda up, g, pref, cd: exercise.advise(up, g, pref, cd)
            rk["user_profile"] = args[0] if len(args) > 0 else kwargs.get("user_profile", {})
            rk["goal"] = args[1] if len(args) > 1 else kwargs.get("goal", "保持健康")
            rk["preferences"] = args[2] if len(args) > 2 else kwargs.get("preferences", "")
            rk["chronic_diseases"] = args[3] if len(args) > 3 else kwargs.get("chronic_diseases", [])

        # 透传用户健康数据（今日饮食/近期运动/身体指标），供 mode_router 自动推导上下文注入 prompt
        for field in ("health_snapshot", "today_diet", "today_diet_total", "recent_exercise", "today_body_metrics", "activity_level"):
            if field in kwargs and kwargs[field]:
                rk.setdefault(field, kwargs[field])
        return rk

    def parse_meal(self, text: str, meal_type: str = "") -> dict:
        """解析自然语言饮食描述，返回结构化营养数据

        参数:
            text: 自然语言描述，如 "早餐吃了2个鸡蛋和1碗燕麦"
            meal_type: 可选，指定餐次类型（"早餐"/"午餐"/"晚餐"）

        返回:
            包含结构化食物项、营养总计、警告信息的 JSON
        """
        return self.process("nlu_parse", text, meal_type)

    def _unified_fallback(self, agent_name: str, kwargs: dict, args: tuple) -> Any:
        """统一离线兜底 — 通过注册表分发，新增 Agent 只需注册对应 handler"""
        handler = self._fallback_handlers.get(agent_name)
        if handler:
            return handler(args, kwargs)

        if not self._local_engine:
            return {
                "error": f"Agent {agent_name} 调用失败，无可用兜底引擎",
                "fallback": True,
                "template_type": "none",
            }

        return {
            "error": f"Agent {agent_name} 调用失败，本地兜底暂不支持此场景",
            "fallback": True,
            "template_type": "generic_fallback",
        }

    def extract_memory(self, user_id: int, messages: list) -> dict:
        """提取用户长期记忆"""
        if self._memory_extractor:
            return self._memory_extractor.extract_from_dialogue(user_id, messages)
        return {}


# 全局单例
orchestrator = AgentOrchestrator()
