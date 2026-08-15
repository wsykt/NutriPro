"""prompts 包一致性守护测试（A/C 双模式模板）。

架构收敛后 prompt 模板位于 prompts/ 包，本测试防止两类回归：
1. A（REWRITE_PROMPTS）与 C（CLOUD_PROMPTS）模板键集漂移（新增功能漏配一侧）
2. 模板占位符与 _build_prompt_params 支持参数不一致（运行时 .format() 抛 KeyError）

本测试仅依赖 prompts 包（零运行时依赖），无需 LLM/向量库即可运行：
    python -m pytest tests/unit/test_prompts_consistency.py
"""

import re

from prompts import REWRITE_PROMPTS, CLOUD_PROMPTS

# _build_prompt_params（mode_router.py）按功能支持的参数（含公共参数）
_COMMON_PARAMS = {"template_content", "user_derived_context"}
SUPPORTED_PARAMS = {
    "qa": _COMMON_PARAMS | {"question", "user_profile"},
    "diet_plan": _COMMON_PARAMS | {"user_profile", "goal", "restrictions"},
    "food_recommend": _COMMON_PARAMS | {"ingredients", "crowd_type", "goal"},
    "exercise": _COMMON_PARAMS | {"user_profile", "goal", "preferences", "chronic_diseases"},
}

_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def _extract_placeholders(template: str) -> set:
    """提取模板中的 {占位符}（忽略 JSON 转义的 {{ }}）"""
    return set(_PLACEHOLDER_RE.findall(template))


def test_rewrite_and_cloud_have_same_keys():
    assert set(REWRITE_PROMPTS.keys()) == set(CLOUD_PROMPTS.keys()), (
        f"A/C 模板键集不一致：A={sorted(REWRITE_PROMPTS.keys())} "
        f"C={sorted(CLOUD_PROMPTS.keys())}"
    )


def test_no_empty_templates():
    for name, tmpl in {**REWRITE_PROMPTS, **CLOUD_PROMPTS}.items():
        assert tmpl and tmpl.strip(), f"模板为空：{name}"


def test_placeholders_match_supported_params():
    for func_type, tmpl in {**REWRITE_PROMPTS, **CLOUD_PROMPTS}.items():
        assert func_type in SUPPORTED_PARAMS, f"未知功能类型：{func_type}"
        placeholders = _extract_placeholders(tmpl)
        unsupported = placeholders - SUPPORTED_PARAMS[func_type]
        assert not unsupported, (
            f"{func_type} 模板含未支持占位符 {sorted(unsupported)}（支持："
            f"{sorted(SUPPORTED_PARAMS[func_type])}）"
        )


def test_placeholders_are_used():
    """每个模板至少应引用一个动态参数（纯静态模板无意义）"""
    for func_type, tmpl in {**REWRITE_PROMPTS, **CLOUD_PROMPTS}.items():
        placeholders = _extract_placeholders(tmpl)
        assert placeholders, f"{func_type} 模板没有任何动态占位符"
