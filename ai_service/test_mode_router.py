"""ModeRouter 双模式切换逻辑单元测试

重点验证：
1. high_performance=true  → C_direct 路径（直接云端，无本地校验）
2. high_performance=false → A 模板召回 + 本地改写 → 校验失败回退 C 路径
3. 结构化输出的 _meta 元信息注入
4. 参数解包正确（diet / food_recommend / exercise / qa 四种）

使用 Mock 避免真实 LLM 调用，仅测流程分发逻辑。
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

# 确保 health/ai_service 在路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestModeRouterInit(unittest.TestCase):
    """ModeRouter 初始化 & 依赖注入"""

    def test_init_and_inject(self):
        from services.mode_router import ModeRouter
        mr = ModeRouter()
        self.assertIsNone(mr._llm)
        self.assertIsNone(mr._retriever)

        mock_llm = MagicMock()
        mock_ret = MagicMock()
        mock_le = MagicMock()
        mr.init(llm=mock_llm, retriever=mock_ret, local_engine=mock_le)
        self.assertIs(mr._llm, mock_llm)
        self.assertIs(mr._retriever, mock_ret)
        self.assertIs(mr._local_engine, mock_le)


class TestModeRouterRouting(unittest.TestCase):
    """核心路由分发测试（Mock LLM/Retriever/Engine）"""

    def setUp(self):
        from services.mode_router import ModeRouter
        self.mr = ModeRouter()
        self.mock_llm = MagicMock()
        self.mock_ret = MagicMock()
        self.mock_le = MagicMock()
        # mock count() 返回 0 跳过真实检索
        self.mock_ret.count.return_value = 0
        self.mr.init(llm=self.mock_llm, retriever=self.mock_ret, local_engine=self.mock_le)
        # 关闭相关性校验（本测试聚焦路由分发逻辑；相关性校验在 test_kb_dedup.py 单测）
        self.mr._relevance_check = False

        # 给 mock_le 增加几个 fallback 方法（返回字典）
        self.mock_le.fallback_diet_plan.return_value = {
            "goal": "均衡饮食", "total_calories": 2000,
            "daily_plan": {"早餐": [{"food": "鸡蛋", "portion": "1个"}],
                           "午餐": [{"food": "米饭", "portion": "100g"}],
                           "晚餐": [{"food": "蔬菜", "portion": "200g"}]},
            "nutrition_breakdown": {"protein": 80, "carbohydrate": 250, "fat": 60},
            "tips": [], "avoided_foods": [], "replaced_foods": [],
        }
        self.mock_le.fallback_food_recommend.return_value = {
            "total_meals": 3, "meal_plan": [
                {"meal_type": "早餐", "name": "a", "ingredients": [], "cook_method": "", "calories_estimate": 100, "protein_estimate": 10, "tags": []},
                {"meal_type": "午餐", "name": "b", "ingredients": [], "cook_method": "", "calories_estimate": 100, "protein_estimate": 10, "tags": []},
                {"meal_type": "晚餐", "name": "c", "ingredients": [], "cook_method": "", "calories_estimate": 100, "protein_estimate": 10, "tags": []},
            ], "total_calories": 1200, "total_protein": 50, "tips": [], "missing_ingredients": [],
        }
        self.mock_le.fallback_exercise_advice.return_value = {
            "goal": "减脂", "weekly_schedule": [
                {"day": "周一", "exercise_type": "快走", "duration": "30", "intensity": "中", "description": "", "calories_burn_estimate": 150},
                {"day": "周二", "exercise_type": "力量", "duration": "30", "intensity": "中", "description": "", "calories_burn_estimate": 150},
                {"day": "周三", "exercise_type": "瑜伽", "duration": "30", "intensity": "低", "description": "", "calories_burn_estimate": 150},
            ],
            "weekly_total_minutes": 90, "weekly_total_calories": 450,
            "warm_up": "", "cool_down": "", "precautions": [], "progression_plan": "",
        }
        self.mock_le.answer_health_query.return_value = (
            "关于高血压的建议：1.限制盐摄入；2.适量运动；3.控制体重；4.少喝酒。"
            "温馨提示：本内容仅供膳食科普参考，不构成医疗建议，慢性病请遵从执业医师指导。"
        )

    # ---- 高性能模式：diet_plan ----
    def test_diet_high_performance_routes_c_direct(self):
        """diet_plan 高性能模式必须走 C_direct 且 mode=high_performance"""
        self.mock_llm.chat_json.return_value = {
            "goal": "减脂", "total_calories": 1800,
            "daily_plan": {
                "早餐": [{"food": "燕麦", "portion": "50g"}],
                "午餐": [{"food": "鸡胸", "portion": "120g"}],
                "晚餐": [{"food": "沙拉", "portion": "200g"}],
                "加餐": [{"food": "酸奶", "portion": "150g"}],
            },
            "nutrition_breakdown": {"protein": 100, "carbohydrate": 180, "fat": 50},
            "tips": ["多喝水"], "avoided_foods": [], "replaced_foods": [],
        }
        result = self.mr.route(
            "diet_plan", high_performance=True,
            user_profile={"age": 30, "crowd_type": "健身"}, goal="减脂",
        )
        self.assertEqual(result["mode"], "high_performance")
        self.assertEqual(result["route"], "C_direct")
        self.assertTrue(result["validation"].get("skipped"))
        # 高性能模式下应该调用 chat_json (云端)，而不是 local_engine fallback
        self.mock_llm.chat_json.assert_called_once()
        self.mock_le.fallback_diet_plan.assert_not_called()

    # ---- 正常模式：diet_plan 走 A (本地) ----
    def test_diet_normal_uses_a_when_template_ok(self):
        """正常模式 + 本地 fallback 输出合法 → route=A_template_local"""
        # count=0 → 无模板 → _run_local_rewrite 直接走 local_engine.fallback_diet_plan
        result = self.mr.route(
            "diet_plan", high_performance=False,
            user_profile={"age": 45, "gender": "男", "crowd_type": "高血压",
                           "chronic_diseases": ["高血压"]},
            goal="控血压",
        )
        self.assertEqual(result["mode"], "normal")
        # local_engine fallback 的结果是合法的，所以应该走 A_template_local
        self.assertEqual(result["route"], "A_template_local")
        self.assertTrue(result["validation"]["passed"])
        self.mock_le.fallback_diet_plan.assert_called_once()
        # A 方案通过校验，所以不会回退 C，云端不会被调用
        self.mock_llm.chat_json.assert_not_called()

    # ---- 正常模式：food_recommend A 方案校验通过 ----
    def test_food_normal_a_passes(self):
        """食材推荐：A 方案输出合法 → 不调用云端"""
        result = self.mr.route(
            "food_recommend", high_performance=False,
            ingredients=["鸡蛋", "西红柿"],
            crowd_type="普通人", goal="减脂",
        )
        self.assertEqual(result["mode"], "normal")
        self.assertEqual(result["route"], "A_template_local")
        self.mock_llm.chat_json.assert_not_called()

    # ---- 正常模式：exercise A 方案校验失败 → 回退 C ----
    def test_exercise_normal_a_fails_fallback_c(self):
        """运动方案 A 输出不合法 → route=C_fallback，且调用了云端 chat_json"""
        # 让 local fallback 返回一个缺字段的结果：weekly_schedule 只有2天（<3）
        self.mock_le.fallback_exercise_advice.return_value = {
            "goal": "减脂",
            "weekly_schedule": [
                {"day": "周一", "exercise_type": "快走", "duration": "30", "intensity": "中", "description": "", "calories_burn_estimate": 150},
                {"day": "周二", "exercise_type": "力量", "duration": "30", "intensity": "中", "description": "", "calories_burn_estimate": 150},
                # 故意少一天 → 触发校验失败
            ],
            "weekly_total_minutes": 60, "weekly_total_calories": 300,
            "warm_up": "", "cool_down": "", "precautions": [], "progression_plan": "",
        }
        # 云端 chat_json 返回合法结果
        self.mock_llm.chat_json.return_value = {
            "goal": "减脂",
            "weekly_schedule": [
                {"day": f"周{x}", "exercise_type": "快走", "duration": "30",
                 "intensity": "中", "description": "", "calories_burn_estimate": 150}
                for x in "一二三四五六日"
            ][:5],
            "weekly_total_minutes": 150, "weekly_total_calories": 750,
            "warm_up": "动态拉伸", "cool_down": "静态拉伸",
            "precautions": ["注意补水"], "progression_plan": "",
        }
        result = self.mr.route(
            "exercise", high_performance=False,
            user_profile={"age": 60, "crowd_type": "老年"}, goal="保持健康",
            preferences="", chronic_diseases=["高血压"],
        )
        # A 方案校验失败 → 回退 C 方案
        self.assertEqual(result["route"], "C_fallback")
        self.assertEqual(result["mode"], "normal")
        self.assertIn("a_issues", result["validation"])
        # chat_json 被调用（云端 fallback）
        self.mock_llm.chat_json.assert_called()

    # ---- QA 高性能模式 ----
    def test_qa_high_performance_calls_cloud_chat(self):
        """健康问答 高性能模式 → 直接调用 llm.chat (云端)"""
        self.mock_llm.chat.return_value = "关于高血压，请：1.限盐；2.多运动；3.控体重；4.限酒。"
        result = self.mr.route(
            "qa", high_performance=True,
            question="高血压吃什么好？",
            user_profile={"age": 50, "crowd_type": "高血压"},
            health_snapshot={}, chronic_diseases=["高血压"],
        )
        self.assertEqual(result["mode"], "high_performance")
        self.assertEqual(result["route"], "C_direct")
        self.mock_llm.chat.assert_called_once()


class TestOrchestratorIntegration(unittest.TestCase):
    """orchestrator.process / chat 的参数解包和 _meta 注入（手动注入 mock 依赖）"""

    def setUp(self):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        # 直接 new 一个 AgentOrchestrator，不调用 init()，手动注入各依赖
        from agent.orchestrator import AgentOrchestrator
        self.orch = AgentOrchestrator()

        # 手动注入 mode_router mock
        self.mock_mr = MagicMock()
        self.mock_mr.route.return_value = {
            "result": {"goal": "test", "total_calories": 2000, "daily_plan": {}, "nutrition_breakdown": {}, "tips": [], "avoided_foods": [], "replaced_foods": []},
            "mode": "high_performance",
            "route": "C_direct",
            "timing_ms": {"cloud_ms": 500, "total_ms": 500},
            "validation": {"skipped": True, "reason": "high_performance模式"},
        }
        self.orch._mode_router = self.mock_mr
        # 其他依赖用空 mock 填充，防止 getattr 报错
        self.orch._llm = MagicMock()
        self.orch._retriever = MagicMock()
        self.orch._store = MagicMock()
        self.orch._store.get_context.return_value = []
        self.orch._store.create_conversation.return_value = "conv_123"
        self.orch._memory_extractor = MagicMock()
        self.orch._local_engine = MagicMock()

    def test_process_diet_high_performance_param(self):
        """orchestrator.process("diet", up, goal, high_performance=True) → mode_router.route 收到 high_performance=True"""
        user_profile = {"age": 30}
        goal = "减脂"
        self.orch.process("diet", user_profile, goal, high_performance=True)
        self.mock_mr.route.assert_called_once()
        kwargs = self.mock_mr.route.call_args.kwargs
        self.assertTrue(kwargs["high_performance"])
        self.assertEqual(kwargs["func_type"], "diet_plan")
        self.assertIs(kwargs["user_profile"], user_profile)
        self.assertEqual(kwargs["goal"], goal)

    def test_process_food_recommend_param_unpack(self):
        """food_recommend 参数解包"""
        ings = ["鸡蛋", "西红柿"]
        self.orch.process("food_recommend", ings, "普通人", "健康饮食", high_performance=False)
        kwargs = self.mock_mr.route.call_args.kwargs
        self.assertFalse(kwargs["high_performance"])
        self.assertEqual(kwargs["func_type"], "food_recommend")
        self.assertEqual(kwargs["ingredients"], ings)
        self.assertEqual(kwargs["crowd_type"], "普通人")
        self.assertEqual(kwargs["goal"], "健康饮食")

    def test_process_exercise_param_unpack(self):
        """exercise 参数解包（含慢性病人群）"""
        up = {"age": 65, "crowd_type": "老年"}
        chronic = ["高血压"]
        self.orch.process("exercise", up, "保持健康", "散步", chronic, high_performance=True)
        kwargs = self.mock_mr.route.call_args.kwargs
        self.assertTrue(kwargs["high_performance"])
        self.assertEqual(kwargs["func_type"], "exercise")
        self.assertIs(kwargs["user_profile"], up)
        self.assertEqual(kwargs["goal"], "保持健康")
        self.assertEqual(kwargs["preferences"], "散步")
        self.assertEqual(kwargs["chronic_diseases"], chronic)

    def test_process_result_injects_meta(self):
        """结构化结果注入 _meta 字段（前端展示模式信息）"""
        result = self.orch.process("diet", {"age": 30}, "减脂", high_performance=True)
        self.assertIn("_meta", result)
        self.assertTrue(result["_meta"]["high_performance"])
        self.assertEqual(result["_meta"]["mode"], "high_performance")
        self.assertEqual(result["_meta"]["route"], "C_direct")


if __name__ == "__main__":
    # 输出彩色结果
    unittest.main(verbosity=2)
