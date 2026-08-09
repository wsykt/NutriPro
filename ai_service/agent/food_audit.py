from agent.base import BaseAgent
from constants.food_units import FOOD_CALORIE_PER_100G, BEVERAGE_CALORIE_PER_100ML
import re

FOOD_AUDIT_PROMPT = """你是食材信息初审辅助Agent。

输入：用户提交食材：名称、分类、热量、蛋白质、脂肪、碳水等营养数据。

审核规则：
1. 识别和现有食材重名及近义词（如土鸡蛋/鸡蛋、五花肉/三层肉）；
2. 热量区间0~1000kcal/100g，超出判定异常；
3. 识别无效名称、广告、乱码；
4. 校验食材分类与名称是否匹配（如"鸡蛋"分类填"蔬菜"需标记风险）；
5. 区分系统内置食材和用户自定义食材，自定义食材审核标准更严格。

输出JSON：
{
  "status": "pass",
  "calories": 250,
  "protein": 15,
  "fat": 18,
  "carbohydrate": 10,
  "nutrition_tags": ["高蛋白", "高脂肪"],
  "advice": "针对该食物的健康建议",
  "audit_level": "pass",
  "risk_desc": "",
  "duplicate_info": {"is_duplicate": false, "similar_names": []},
  "is_system_food": true,
  "category_mismatch": false,
  "category_suggestion": ""
}

重要：仅作为辅助参考，不能自动审核通过食材。

Few-Shot 示例：
输入：{"food_name":"鸡蛋","category":"蛋类","calorie":144,"protein":13.3,"fat":8.8,"carb":2.8,"portion":"100g"}
输出：{"status":"pass","calories":144,"protein":13.3,"fat":8.8,"carbohydrate":2.8,"nutrition_tags":["高蛋白"],"advice":"鸡蛋是优质蛋白质来源，建议每天1-2个。","audit_level":"pass","risk_desc":"","duplicate_info":{"is_duplicate":false,"similar_names":["土鸡蛋","柴鸡蛋"]},"is_system_food":true,"category_mismatch":false,"category_suggestion":""}

输入：{"food_name":"超级燃脂瘦身丸","category":"保健","calorie":0,"protein":0,"fat":0,"carb":0,"portion":"1粒"}
输出：{"status":"reject","calories":0,"protein":0,"fat":0,"carbohydrate":0,"nutrition_tags":[],"advice":"无效名称或广告，拒绝审核。","audit_level":"reject","risk_desc":"无效名称或广告宣传","duplicate_info":{"is_duplicate":false,"similar_names":[]},"is_system_food":false,"category_mismatch":true,"category_suggestion":"无法确定合适分类"}"""

SYNONYM_MAP = {
    "鸡蛋": ["土鸡蛋", "柴鸡蛋", "笨鸡蛋", "草鸡蛋", "洋鸡蛋"],
    "五花肉": ["三层肉", "五花腩", "腩肉"],
    "猪瘦肉": ["瘦肉", "猪里脊", "里脊", "猪腿肉"],
    "鸡胸肉": ["鸡胸脯", "鸡大胸", "鸡胸"],
    "西红柿": ["番茄", "洋柿子"],
    "土豆": ["马铃薯", "洋芋", "山药蛋"],
    "西兰花": ["青花菜", "绿花菜"],
    "白菜": ["大白菜", "黄芽菜"],
    "黄瓜": ["青瓜"],
    "胡萝卜": ["红萝卜"],
    "苹果": ["红苹果", "青苹果", "富士苹果"],
    "香蕉": ["芭蕉"],
    "橙子": ["柳橙", "甜橙"],
    "牛奶": ["鲜奶", "鲜牛奶"],
    "酸奶": ["酸牛奶", "优酸乳"],
    "豆浆": ["豆奶"],
    "米饭": ["白米饭", "大米饭"],
    "面条": ["挂面", "拉面", "方便面"],
    "馒头": ["白面馒头", "馍"],
    "面包": ["吐司", "面包片"],
    "蛋糕": ["奶油蛋糕"],
    "饼干": ["曲奇", "酥饼"],
    "巧克力": ["黑巧克力", "牛奶巧克力"],
    "坚果": ["干果", "果仁"],
    "冰淇淋": ["雪糕", "冰激凌"],
    "薯片": ["洋芋片", "土豆片"],
    "玉米": ["苞米", "玉米粒"],
    "红薯": ["番薯", "地瓜", "山芋"],
    "紫薯": ["紫红薯"],
    "菠菜": ["菠薐菜"],
    "生菜": ["西生菜"],
    "芹菜": ["西芹"],
    "豆角": ["四季豆", "长豆角"],
    "南瓜": ["倭瓜"],
    "豆腐": ["嫩豆腐", "老豆腐", "南豆腐", "北豆腐"],
    "腐竹": ["腐皮"],
    "鸡腿": ["鸡大腿", "琵琶腿"],
    "鸡翅": ["鸡翅膀", "翅中", "翅根"],
    "牛肉": ["牛腱子", "牛腩", "牛里脊"],
    "羊肉": ["羊腿肉", "羊排"],
    "鱼肉": ["鱼片", "鱼块"],
    "虾仁": ["虾", "海虾", "河虾"],
    "三文鱼": ["大马哈鱼"],
    "橙子": ["橘子", "柑"],
    "梨": ["雪梨", "鸭梨"],
    "桃子": ["水蜜桃"],
    "西瓜": ["麒麟瓜", "黑美人"],
    "葡萄": ["提子"],
    "草莓": ["红莓", "士多啤梨"],
    "蓝莓": ["越橘"],
    "芒果": ["杧果"],
    "荔枝": ["离枝"],
    "龙眼": ["桂圆"],
}

CATEGORY_KEYWORDS = {
    "蔬菜": ["白菜", "菠菜", "西兰花", "西红柿", "黄瓜", "胡萝卜", "土豆", "豆角", "南瓜", "生菜", "芹菜", "莲藕", "茄子", "青椒", "韭菜", "葱", "蒜"],
    "水果": ["苹果", "香蕉", "橙子", "西瓜", "葡萄", "草莓", "蓝莓", "芒果", "荔枝", "龙眼", "梨", "桃子", "菠萝", "柚子"],
    "肉类": ["猪肉", "牛肉", "羊肉", "鸡肉", "鸭肉", "鱼肉", "虾仁", "三文鱼", "鸡腿", "鸡翅", "鸡胸肉", "五花肉"],
    "蛋类": ["鸡蛋", "鸭蛋", "鹌鹑蛋", "鹅蛋"],
    "奶类": ["牛奶", "酸奶", "奶酪", "奶粉"],
    "豆制品": ["豆腐", "腐竹", "豆浆", "豆干", "豆皮"],
    "主食": ["米饭", "面条", "馒头", "面包", "玉米", "红薯", "燕麦", "糙米", "小米"],
    "零食": ["饼干", "蛋糕", "巧克力", "薯片", "坚果", "冰淇淋"],
    "饮料": ["奶茶", "可乐", "果汁", "咖啡", "啤酒", "红酒"],
}

SYSTEM_FOODS = set([
    "红烧肉", "五花肉", "猪蹄", "回锅肉", "牛肉", "羊肉", "猪肉", "鸡肉", "鸭肉",
    "鸡胸肉", "鸡腿", "鸡翅", "牛肉", "牛腩", "牛腱", "羊腿", "排骨",
    "三文鱼", "虾仁", "鱼肉", "鳕鱼", "金枪鱼", "虾", "螃蟹", "龙虾",
    "鸡蛋", "鸭蛋", "鹌鹑蛋", "鹅蛋",
    "牛奶", "酸奶", "奶酪", "奶粉",
    "西兰花", "菠菜", "白菜", "生菜", "西红柿", "黄瓜", "胡萝卜", "豆角",
    "土豆", "洋葱", "大蒜", "辣椒", "茄子", "青椒", "韭菜", "芹菜", "莲藕",
    "苹果", "香蕉", "橙子", "西瓜", "葡萄", "草莓", "蓝莓", "芒果", "荔枝",
    "龙眼", "梨", "桃子", "菠萝", "柚子", "猕猴桃", "樱桃", "李子",
    "米饭", "面条", "馒头", "小米粥", "燕麦", "糙米", "红薯", "玉米",
    "面包", "蛋糕", "饼干", "巧克力", "薯片", "坚果", "冰淇淋",
    "奶茶", "可乐", "果汁", "咖啡", "啤酒", "红酒", "雪碧", "能量饮料",
    "豆腐", "腐竹", "豆浆", "豆干", "豆皮",
    "核桃", "杏仁", "花生", "腰果", "开心果",
])


class FoodAuditAgent(BaseAgent):

    @staticmethod
    def _find_synonyms(food_name: str) -> list:
        synonyms = []
        for standard_name, alternatives in SYNONYM_MAP.items():
            if standard_name in food_name:
                synonyms.extend([alt for alt in alternatives if alt != food_name])
            for alt in alternatives:
                if alt in food_name and standard_name != food_name:
                    synonyms.append(standard_name)
        return list(set(synonyms))

    @staticmethod
    def _check_category_match(food_name: str, category: str) -> tuple:
        if not category:
            return False, ""
        
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if cat in category or category in cat:
                for keyword in keywords:
                    if keyword in food_name:
                        return True, ""
                return False, f"建议分类：{', '.join([k for k, v in CATEGORY_KEYWORDS.items() if any(kw in food_name for kw in v)][:3])}"
        
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if any(keyword in food_name for keyword in keywords):
                return False, f"建议分类：{cat}"
        
        return False, "无法确定合适分类"

    @staticmethod
    def _is_system_food(food_name: str) -> bool:
        if food_name in SYSTEM_FOODS:
            return True
        for sys_food in SYSTEM_FOODS:
            if sys_food in food_name or food_name in sys_food:
                return True
        return False

    @staticmethod
    def audit(food_data: dict) -> dict:
        food_name = food_data.get("food_name", "")
        portion = food_data.get("portion", "")
        category = food_data.get("category", "")

        is_system_food = FoodAuditAgent._is_system_food(food_name)
        synonyms = FoodAuditAgent._find_synonyms(food_name)
        category_match, category_suggestion = FoodAuditAgent._check_category_match(food_name, category)

        try:
            messages = [
                {"role": "system", "content": "你是一个食材信息初审专家。只输出JSON。"},
                {"role": "user", "content": FOOD_AUDIT_PROMPT + f"\n\n待审核食材：{food_data}"},
            ]
            parsed = FoodAuditAgent.chat_json(messages)
        except Exception:
            parsed = {}

        if not parsed:
            parsed = {}

        if "calories" not in parsed or parsed.get("calories") == 0:
            parsed["calories"] = FoodAuditAgent._estimate_calories(food_name, portion)

        calories_value = parsed.get("calories", 0)
        try:
            calories_value = int(calories_value)
        except (ValueError, TypeError):
            calories_value = 0
        
        if calories_value > 500:
            tags = parsed.get("nutrition_tags", [])
            if not isinstance(tags, list):
                tags = []
            if "高热量" not in tags:
                tags.append("高热量")
            parsed["nutrition_tags"] = tags
            advice = parsed.get("advice", "")
            if not isinstance(advice, str):
                advice = ""
            if "适量" not in advice:
                parsed["advice"] = advice + " 建议适量食用。"

        risk_desc = parsed.get("risk_desc", "")
        
        if synonyms:
            risk_desc += f" [检测到近义词：{', '.join(synonyms)}]"
        
        if not category_match and category:
            risk_desc += f" [分类可能不匹配，{category_suggestion}]"
        
        if not is_system_food:
            risk_desc += " [用户自定义食材，建议人工审核]"

        audit_level = parsed.get("audit_level", "pass")
        if risk_desc:
            audit_level = "review"

        return {
            "status": parsed.get("status", "pass"),
            "calories": parsed.get("calories", 0),
            "protein": parsed.get("protein", 0),
            "fat": parsed.get("fat", 0),
            "carbohydrate": parsed.get("carbohydrate", 0),
            "nutrition_tags": parsed.get("nutrition_tags", []),
            "advice": parsed.get("advice", ""),
            "audit_level": audit_level,
            "risk_desc": risk_desc.strip(),
            "duplicate_info": {
                "is_duplicate": len(synonyms) > 0,
                "similar_names": synonyms,
            },
            "is_system_food": is_system_food,
            "category_mismatch": not category_match,
            "category_suggestion": category_suggestion,
        }

    @staticmethod
    def _estimate_calories(food_name: str, portion: str) -> int:
        weight = 100
        is_beverage = "毫升" in portion or "ml" in portion.lower()

        if "克" in portion:
            try:
                weight = int(''.join(filter(str.isdigit, portion)))
            except:
                pass
        elif "毫升" in portion or "ml" in portion.lower():
            try:
                weight = int(''.join(filter(str.isdigit, portion)))
            except:
                pass

        if is_beverage:
            for key, cal_per_100ml in BEVERAGE_CALORIE_PER_100ML.items():
                if key in food_name:
                    return int(cal_per_100ml * weight / 100)

        for key, cal_per_100g in FOOD_CALORIE_PER_100G.items():
            if key in food_name:
                return int(cal_per_100g * weight / 100)

        return int(150 * weight / 100)


agent = FoodAuditAgent()