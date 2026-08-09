"""运动建议 Agent

基于用户 BMI、慢病情况、健身目标，生成个性化运动方案。
降级走 local_fallback_engine.py（由 orchestrator 统一处理）
免责声明走 services/disclaimer.py
"""

from agent.base import BaseAgent

EXERCISE_ADVICE_PROMPT = """你是运动健康指导Agent。

输入：
1. 用户档案：年龄、性别、身高、体重、BMI、人群标签
2. 健康目标（减脂/增肌/保持健康/康复/控糖）
3. 慢性病信息（如果有）
4. 运动偏好（如果有）

任务：
根据用户身体状况和健康目标，设计安全、科学、可执行的运动方案。

输出JSON：
{
  "goal": "用户目标",
  "weekly_schedule": [
    {"day": "周一", "exercise_type": "运动类型", "duration": "时长（分钟）", "intensity": "低/中/高", "description": "详细说明", "calories_burn_estimate": 200}
  ],
  "weekly_total_minutes": 150,
  "weekly_total_calories": 1000,
  "warm_up": "热身建议",
  "cool_down": "拉伸建议",
  "precautions": ["注意事项1", "注意事项2"],
  "progression_plan": "进阶计划"
}

约束：
- 每周推荐运动量不超过 WHO 建议上限（健康成人300分钟/周）
- 慢病患者必须标注注意事项和禁忌动作
- 不提供医疗诊断
- 仅输出JSON，禁止额外文字"""


class ExerciseAdviceAgent(BaseAgent):

    @staticmethod
    def advise(user_profile: dict, goal: str = "保持健康", preferences: str = "", chronic_diseases: list = None) -> dict:
        if chronic_diseases is None:
            chronic_diseases = []

        bmi = user_profile.get("bmi", 0)
        age = user_profile.get("age", 30)
        gender = user_profile.get("gender", "男")
        crowd = user_profile.get("crowd_type", "普通人")

        # 构造 profile 字符串
        profile_str = f"年龄{age}岁，{gender}，BMI{bmi:.1f}，人群标签{crowd}"
        if chronic_diseases:
            profile_str += f"，慢病：{'、'.join(chronic_diseases)}"

        # 知识库检索
        kb_context = ExerciseAdviceAgent.get_kb_context(f"{crowd} {goal} 运动建议")

        prompt = EXERCISE_ADVICE_PROMPT + f"\n\n用户档案：{profile_str}\n运动目标：{goal}\n运动偏好：{preferences}"
        if kb_context:
            prompt += f"\n{kb_context}"

        messages = [
            {"role": "system", "content": "你是专业运动健康指导专家。只输出JSON。"},
            {"role": "user", "content": prompt},
        ]

        parsed = ExerciseAdviceAgent.chat_json(messages)
        if parsed and "weekly_schedule" in parsed:
            parsed["user_profile"] = profile_str
            # 添加免责声明
            precautions = parsed.get("precautions", [])
            disclaimer = BaseAgent.add_disclaimer("")
            if disclaimer:
                precautions.append(disclaimer)
                parsed["precautions"] = precautions
            return parsed

        raise ValueError("运动建议生成失败")


agent = ExerciseAdviceAgent()
