import json
import os

# 生成演示数据到正确路径
output_path = r"c:\Users\13425\Desktop\个人健康助手\health\ai_service\crawler\demo_food_data.json"

demo_data = [
    {
        "name": "小麦粉(标准粉)",
        "source_url": "https://nlc.chinanutri.cn/fq/food/123",
        "nutrition": {
            "energy_kcal": 354.0,
            "protein_g": 11.2,
            "fat_g": 1.5,
            "carbohydrate_g": 73.6,
            "fiber_g": 2.1,
            "sodium_mg": 5.0,
            "vitamin_a_ug": 0.0,
            "vitamin_c_mg": 0.0,
            "calcium_mg": 18.0,
            "iron_mg": 3.5,
            "zinc_mg": 1.83
        }
    },
    {
        "name": "稻米(大米)",
        "source_url": "https://nlc.chinanutri.cn/fq/food/124",
        "nutrition": {
            "energy_kcal": 346.0,
            "protein_g": 7.4,
            "fat_g": 0.8,
            "carbohydrate_g": 77.9,
            "fiber_g": 0.7,
            "sodium_mg": 3.8,
            "vitamin_a_ug": 0.0,
            "vitamin_c_mg": 0.0,
            "calcium_mg": 13.0,
            "iron_mg": 2.3,
            "zinc_mg": 1.7
        }
    }
]

# 确保目录存在
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# 写入文件
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(demo_data, f, ensure_ascii=False, indent=2)

print(f"演示数据已生成: {output_path}")