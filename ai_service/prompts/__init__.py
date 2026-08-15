"""提示词模板包（A/C 双模式）。

架构收敛：prompt 模板从 services/mode_router.py 拆出，作为独立数据模块与
调度逻辑解耦。修改任一功能的 prompt 只需改本包对应文件：
- rewrite.py  → A 方案（本地模板改写）
- cloud.py    → C 方案（云端直出）

注意：本包必须保持零运行时依赖（仅标准库），以便独立单测与审查。
"""

from prompts.rewrite import REWRITE_PROMPTS
from prompts.cloud import CLOUD_PROMPTS

__all__ = ["REWRITE_PROMPTS", "CLOUD_PROMPTS"]
