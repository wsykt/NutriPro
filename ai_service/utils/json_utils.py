import json
import re


def clean_json_string(text: str) -> str:
    if not text:
        return ""

    cleaned = text.strip()

    cleaned = re.sub(r'```json\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)

    cleaned = re.sub(r'<!--[\s\S]*?-->', '', cleaned)
    cleaned = re.sub(r'//.*$', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'/\*[\s\S]*?\*/', '', cleaned)

    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)

    cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
    cleaned = cleaned.replace('\r\n', '\n')

    return cleaned


# ============================================================
# 增强 JSON 修复工具（集中处理所有 Agent 输出）
# ============================================================

def repair_common_issues(text: str) -> str:
    """修复 Agent 输出的常见 JSON 格式问题"""
    if not text:
        return text

    # 1. 修复 trailing commas
    text = re.sub(r',\s*([}\]])', r'\1', text)

    # 2. 修复单引号（先将外部双引号内的内容保护起来）
    # 保护已存在的双引号内容
    protected = {}
    def protect(m):
        idx = len(protected)
        protected[f'__STR{idx}__'] = m.group(1)
        return f'"__STR{idx}__"'
    text = re.sub(r'"([^"]*)"', protect, text)
    # 将剩余单引号替换为双引号
    text = text.replace("'", '"')
    # 恢复被保护的内容
    for key, val in protected.items():
        text = text.replace(f'"{key}"', f'"{val}"')

    # 3. 修复未加引号的 key（{key: value} -> {"key": value}）
    text = re.sub(r'([{,]\s*)([a-zA-Z_]\w*)\s*:', r'\1"\2":', text)

    # 4. 修复中文括号
    text = text.replace('（', '(').replace('）', ')')

    # 5. 修复布尔值和 null 大小写
    text = re.sub(r'(?i)\btrue\b', 'true', text)
    text = re.sub(r'(?i)\bfalse\b', 'false', text)
    text = re.sub(r'(?i)\bnull\b', 'null', text)
    text = re.sub(r'(?i)\bnone\b', 'null', text)

    # 6. 修复未加引号的裸值（"amount": 2个 / "calories": 1800kcal 等本地模型常见错误）
    #    已是合法字符串/数字/布尔/null/对象/数组的值跳过，其余裸值统一加双引号。
    #    值正则排除引号/逗号/花括号/方括号，天然不触碰已加引号的字符串与嵌套结构。
    def _wrap_bare_value(m):
        key_part = m.group(1)
        val = m.group(2).strip()
        # 值为空（如冒号后紧跟引号/花括号前的空格）→ 原样保留
        if not val:
            return m.group(0)
        if val.startswith('"') or val.startswith('{') or val.startswith('['):
            return m.group(0)
        if val in ('true', 'false', 'null'):
            return m.group(0)
        if re.fullmatch(r'-?\d+(?:\.\d+)?', val):
            return m.group(0)
        return f'{key_part}"{val}"'

    text = re.sub(r'("(?:[^"\\]|\\.)*"\s*:\s*)([^",\[{\]}]+)', _wrap_bare_value, text)

    return text


def extract_json_from_agent_response(text: str) -> str:
    """从 Agent 回复中鲁棒提取 JSON 字符串（最外层/嵌套全考虑）"""
    if not text:
        return ""

    text = clean_json_string(text)

    # 尝试直接解析
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    # 尝试修复后解析
    repaired = repair_common_issues(text)
    try:
        json.loads(repaired)
        return repaired
    except json.JSONDecodeError:
        pass

    # 尝试提取 { } 内容（最外层花括号）
    brace_depth = 0
    start = -1
    for i, ch in enumerate(repaired):
        if ch == '{':
            if brace_depth == 0:
                start = i
            brace_depth += 1
        elif ch == '}':
            brace_depth -= 1
            if brace_depth == 0 and start >= 0:
                candidate = repaired[start:i+1]
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    pass
                # 修复后重试
                try:
                    json.loads(repair_common_issues(candidate))
                    return repair_common_issues(candidate)
                except json.JSONDecodeError:
                    pass

    # 尝试提取 [ ] 内容（JSON 数组）
    bracket_depth = 0
    start = -1
    for i, ch in enumerate(repaired):
        if ch == '[':
            if bracket_depth == 0:
                start = i
            bracket_depth += 1
        elif ch == ']':
            bracket_depth -= 1
            if bracket_depth == 0 and start >= 0:
                candidate = repaired[start:i+1]
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    pass

    return repaired


def force_parse_json(text: str, default: dict = None) -> dict:
    """强力 JSON 解析——多策略逐级降级，最大限度容忍格式异常"""
    if default is None:
        default = {}

    if not text:
        return default

    extracted = extract_json_from_agent_response(text)

    # 策略 1：直接解析
    try:
        return json.loads(extracted)
    except json.JSONDecodeError:
        pass

    # 策略 2：逐行扫描找合法 JSON
    try:
        lines = extracted.split('\n')
        json_lines = []
        in_json = False
        brace_count = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith('{'):
                in_json = True
                brace_count += stripped.count('{') - stripped.count('}')
                json_lines.append(line)
            elif in_json:
                brace_count += stripped.count('{') - stripped.count('}')
                json_lines.append(line)
                if brace_count <= 0:
                    break

        if json_lines:
            candidate = '\n'.join(json_lines)
            candidate = repair_common_issues(candidate)
            return json.loads(candidate)
    except (json.JSONDecodeError, IndexError):
        pass

    # 策略 3：修复后重试
    try:
        return json.loads(repair_common_issues(extracted))
    except json.JSONDecodeError:
        pass

    return default


def safe_parse_json(text: str, default: dict = None) -> dict:
    """向后兼容的 JSON 解析入口（委托给 force_parse_json）"""
    return force_parse_json(text, default)


def safe_parse_json_list(text: str, default: list = None) -> list:
    """安全解析 JSON 数组"""
    if default is None:
        default = []

    if not text:
        return default

    text = clean_json_string(text)

    # 尝试直接解析
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # 修复后解析
    text = repair_common_issues(text)
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # 从 response 中提取数组
    try:
        # 先试 { "items": [...] } 结构
        obj = force_parse_json(text)
        if "items" in obj and isinstance(obj["items"], list):
            return obj["items"]
        # 遍历找第一个列表字段
        for val in obj.values():
            if isinstance(val, list):
                return val
    except Exception:
        pass

    return default


def truncate_text(text: str, max_length: int = 2000, suffix: str = "...") -> str:
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def truncate_json_content(data: dict, max_total_length: int = 4000) -> dict:
    if not isinstance(data, dict):
        return data
    
    result = {}
    total_length = 0
    
    for key, value in data.items():
        if isinstance(value, str):
            value_length = len(value)
            if total_length + value_length > max_total_length:
                remaining = max_total_length - total_length
                if remaining > 3:
                    result[key] = value[:remaining - 3] + "..."
                break
            result[key] = value
            total_length += value_length
        elif isinstance(value, (dict, list)):
            json_str = json.dumps(value, ensure_ascii=False)
            value_length = len(json_str)
            if total_length + value_length > max_total_length:
                remaining = max_total_length - total_length
                if remaining > 3:
                    result[key] = json_str[:remaining - 3] + "..."
                break
            result[key] = value
            total_length += value_length
        else:
            result[key] = value
    
    return result


def validate_json_structure(data: dict, required_fields: list = None) -> tuple:
    if required_fields is None:
        required_fields = []
    
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    return len(missing_fields) == 0, missing_fields