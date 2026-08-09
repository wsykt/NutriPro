"""AI 回答质量自动打分器（P3 监控创新）

检测回答中的医疗诊断违规、营养数值错误、幻觉内容。
所有数据基于运行时真实输出，用于可视化监控展示。
"""

import re
from typing import Dict, List, Optional


# 违规医疗诊断模式
FORBIDDEN_DIAGNOSIS_PATTERNS = [
    r'(?:诊断|确诊)[了你]?(?:患有|为|是)\s*[\u4e00-\u9fff]{2,10}(?:病|症|炎|癌|瘤)',
    r'(?:建议|推荐|请).*(?:服用|使用|吃).*(?:药|药物|药品|处方)',
    r'请[你]?(?:立即|马上|尽快).*(?:就医|去医院|看医生|就诊)',
]

# 常见营养数值参考范围 (100g)
NUTRIENT_RANGES = {
    "热量": (0, 900),
    "蛋白质": (0, 100),
    "脂肪": (0, 100),
    "碳水": (0, 100),
    "膳食纤维": (0, 50),
    "钙": (0, 2000),
    "铁": (0, 50),
    "维生素C": (0, 500),
}

# 幻觉关键词（知识库未覆盖的断言）
HALLUCINATION_PATTERNS = [
    r'(?:据我所知|我记得|好像|似乎|可能大概|应该是)\s*(?:没有|不存在|无法)',
    r'(?:绝对|一定|肯定|必然)\s*(?:可以|能|会)\s*(?:治愈|根治|痊愈)',
]


class QualityScorer:
    """自动检测回答质量 — 返回结构化评分"""

    def score(self, question: str, response: str, kb_used: bool = False) -> Dict:
        """对一条 AI 回答进行质量评分

        返回:
        {
            "score": 0-100,
            "issues": [],
            "warnings": [],
            "has_diagnosis": False,
            "has_nutrient_error": False,
            "has_hallucination": False,
            "has_disclaimer": True/False,
            "response_length": int,
        }
        """
        issues = []
        warnings = []
        has_diagnosis = False
        has_nutrient_error = False
        has_hallucination = False

        # 1. 医疗诊断违规检测
        for pattern in FORBIDDEN_DIAGNOSIS_PATTERNS:
            if re.search(pattern, response):
                issues.append("疑似医疗诊断或处方建议")
                has_diagnosis = True
                break

        # 2. 营养数值检测
        for nutrient, (min_v, max_v) in NUTRIENT_RANGES.items():
            matches = re.findall(rf'{nutrient}[约为是]?(\d+(?:\.\d+)?)', response)
            for val in matches:
                v = float(val)
                if v < min_v or v > max_v:
                    warnings.append(f"{nutrient}数值{v}超出正常范围[{min_v},{max_v}]")
                    has_nutrient_error = True

        # 3. 幻觉检测
        for pattern in HALLUCINATION_PATTERNS:
            if re.search(pattern, response):
                warnings.append("检测到不确定性表述（可能为知识库未覆盖内容）")
                has_hallucination = True
                break

        # 4. 免责声明检测
        has_disclaimer = bool(re.search(r'(?:免责|温馨提示|不构成医疗建议|仅供参考)', response))

        # 5. 长度检测
        response_length = len(response)

        # 6. 综合评分
        score = 100
        if has_diagnosis:
            score -= 30
        if has_nutrient_error:
            score -= 10
        if has_hallucination:
            score -= 15
        if not has_disclaimer:
            score -= 5
        if response_length < 30:
            score -= 10
            warnings.append("回答过短（<30字）")
        score = max(0, score)

        return {
            "score": score,
            "issues": issues,
            "warnings": warnings,
            "has_diagnosis": has_diagnosis,
            "has_nutrient_error": has_nutrient_error,
            "has_hallucination": has_hallucination,
            "has_disclaimer": has_disclaimer,
            "response_length": response_length,
            "kb_used": kb_used,
        }


scorer = QualityScorer()
