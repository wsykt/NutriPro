# -*- coding: utf-8 -*-
"""
全人群知识库批量构建脚本
========================
目标：构建500-800张结构化知识卡片
覆盖：普通人、健身用户、孕妇、青少年、老年人、糖尿病患者 + 通用主题
流程：PubMed搜索 → 提纯 → ID去重 → 标题相似合并 → 保存知识库
支持：断点续传、进度保存
"""
import requests
import json
import time
import re
import os
from datetime import datetime

# ======================== 配置 ========================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"

# 知识库保存路径
KB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base")
os.makedirs(KB_DIR, exist_ok=True)
KB_FILE = os.path.join(KB_DIR, "full_knowledge_base.json")
PROGRESS_FILE = os.path.join(KB_DIR, "build_progress.json")

# 目标卡片数
TARGET_CARDS = 600  # 目标600张，范围500-800


# ======================== 7大人群 × 子主题规划 ========================
# 每个子主题搜索3-4篇PubMed文献 + 匹配官方指南
SUBTOPICS_CONFIG = [
    # ========== 1. 普通人（70张目标）==========
    {"group": "普通人", "topic": "均衡营养与膳食模式", "keywords": ["balanced diet dietary patterns adults", "dietary diversity nutritional adequacy"]},
    {"group": "普通人", "topic": "地中海饮食与健康", "keywords": ["Mediterranean diet health outcomes meta-analysis", "Mediterranean diet cardiovascular prevention"]},
    {"group": "普通人", "topic": "DASH饮食与血压管理", "keywords": ["DASH diet blood pressure hypertension", "dietary approaches stop hypertension effectiveness"]},
    {"group": "普通人", "topic": "超加工食品危害", "keywords": ["ultra-processed foods health risks", "processed food consumption chronic disease"]},
    {"group": "普通人", "topic": "膳食纤维与肠道健康", "keywords": ["dietary fiber gut health microbiome", "fiber intake colorectal cancer prevention"]},
    {"group": "普通人", "topic": "饮水与健康", "keywords": ["water intake hydration health adults", "drinking water recommendations daily"]},
    {"group": "普通人", "topic": "早餐与健康表现", "keywords": ["breakfast consumption health outcomes", "breakfast skipping metabolic risk"]},
    {"group": "普通人", "topic": "食物搭配与营养吸收", "keywords": ["food synergy nutrient absorption", "dietary combinations bioavailability enhancement"]},

    # ========== 2. 健身用户（70张目标）==========
    {"group": "健身用户", "topic": "蛋白质需求与时机", "keywords": ["protein requirements resistance training", "protein timing muscle protein synthesis"]},
    {"group": "健身用户", "topic": "运动前后营养补充", "keywords": ["pre post workout nutrition performance", "nutrient timing exercise recovery"]},
    {"group": "健身用户", "topic": "肌酸与运动表现", "keywords": ["creatine supplementation exercise performance", "creatine monohydrate strength training"]},
    {"group": "健身用户", "topic": "BCAA与肌肉恢复", "keywords": ["BCAA supplementation muscle recovery", "branched chain amino acids exercise"]},
    {"group": "健身用户", "topic": "耐力运动营养", "keywords": ["endurance exercise nutrition carbohydrates", "marathon running fueling strategy"]},
    {"group": "健身用户", "topic": "减脂期营养策略", "keywords": ["fat loss diet calorie deficit protein", "cutting diet bodybuilding weight loss"]},
    {"group": "健身用户", "topic": "咖啡因与运动表现", "keywords": ["caffeine exercise performance ergogenic", "caffeine supplementation sports performance"]},
    {"group": "健身用户", "topic": "运动补剂安全性与有效性", "keywords": ["sports supplements safety efficacy evidence", "dietary supplements athletes regulation"]},

    # ========== 3. 孕妇（70张目标）==========
    {"group": "孕妇", "topic": "孕期叶酸与神经管缺陷", "keywords": ["folic acid pregnancy neural tube defects", "folate supplementation prenatal care"]},
    {"group": "孕妇", "topic": "孕期铁缺乏与补充", "keywords": ["iron deficiency pregnancy anemia supplementation", "iron supplementation pregnancy outcomes"]},
    {"group": "孕妇", "topic": "孕期钙与维生素D", "keywords": ["calcium vitamin D pregnancy bone health", "vitamin D deficiency pregnancy complications"]},
    {"group": "孕妇", "topic": "DHA与胎儿大脑发育", "keywords": ["DHA omega-3 fetal brain development", "fish oil pregnancy cognitive development"]},
    {"group": "孕妇", "topic": "孕期体重管理", "keywords": ["pregnancy weight gain guidelines BMI", "gestational weight gain complications"]},
    {"group": "孕妇", "topic": "妊娠糖尿病饮食管理", "keywords": ["gestational diabetes diet management", "GDM nutritional therapy blood glucose"]},
    {"group": "孕妇", "topic": "孕期食物安全与禁忌", "keywords": ["pregnancy food safety listeria mercury", "foods avoid pregnancy foodborne"]},
    {"group": "孕妇", "topic": "哺乳期营养需求", "keywords": ["lactation nutrition breastfeeding diet", "postpartum nutritional requirements lactating"]},

    # ========== 4. 青少年（70张目标）==========
    {"group": "青少年", "topic": "生长发育营养需求", "keywords": ["adolescent growth nutrition requirements", "teenager nutritional needs puberty"]},
    {"group": "青少年", "topic": "钙铁锌与骨骼发育", "keywords": ["adolescent calcium iron zinc deficiency", "teenager bone growth mineral nutrition"]},
    {"group": "青少年", "topic": "早餐与学习表现", "keywords": ["breakfast adolescent academic performance", "school breakfast program cognition"]},
    {"group": "青少年", "topic": "青少年肥胖与饮食干预", "keywords": ["adolescent obesity diet intervention", "teenager weight management nutrition"]},
    {"group": "青少年", "topic": "含糖饮料与代谢风险", "keywords": ["sugar sweetened beverages adolescents metabolic", "soda consumption teenagers obesity diabetes"]},
    {"group": "青少年", "topic": "青少年运动营养", "keywords": ["young athlete nutrition sports performance", "adolescent exercise dietary requirements"]},
    {"group": "青少年", "topic": "饮食障碍与营养干预", "keywords": ["adolescent eating disorders anorexia bulimia", "teenager disordered eating nutritional rehabilitation"]},
    {"group": "青少年", "topic": "维生素D与青少年健康", "keywords": ["vitamin D deficiency adolescents", "teenager vitamin D status bone health"]},

    # ========== 5. 老年人（80张目标）==========
    {"group": "老年人", "topic": "肌少症与蛋白质补充", "keywords": ["sarcopenia protein intake older adults", "muscle loss aging nutrition intervention"]},
    {"group": "老年人", "topic": "骨质疏松与钙维生素D", "keywords": ["osteoporosis calcium vitamin D elderly", "bone fracture prevention older adults nutrition"]},
    {"group": "老年人", "topic": "老年认知衰退与营养", "keywords": ["cognitive decline nutrition elderly", "Alzheimer diet MIND Mediterranean aging"]},
    {"group": "老年人", "topic": "老年营养不良筛查与干预", "keywords": ["malnutrition elderly screening MNA", "older adults undernutrition intervention"]},
    {"group": "老年人", "topic": "老年消化问题与膳食纤维", "keywords": ["elderly constipation fiber intake", "aging gastrointestinal function digestion"]},
    {"group": "老年人", "topic": "老年脱水与饮水管理", "keywords": ["dehydration older adults fluid intake", "elderly hydration management nursing"]},
    {"group": "老年人", "topic": "维生素B12与老年神经健康", "keywords": ["vitamin B12 deficiency elderly neurological", "cobalamin aging cognitive function"]},
    {"group": "老年人", "topic": "老年慢病综合饮食管理", "keywords": ["elderly chronic disease diet management", "older adults multiple comorbidities nutrition"]},

    # ========== 6. 糖尿病患者（80张目标）==========
    {"group": "糖尿病患者", "topic": "血糖指数GI与血糖控制", "keywords": ["glycemic index diabetes blood glucose control", "low GI diet diabetes management"]},
    {"group": "糖尿病患者", "topic": "膳食纤维与血糖调节", "keywords": ["dietary fiber diabetes glycemic control", "soluble fiber insulin resistance improvement"]},
    {"group": "糖尿病患者", "topic": "碳水化合物计数法", "keywords": ["carbohydrate counting diabetes management", "carb counting type 1 type 2 diabetes"]},
    {"group": "糖尿病患者", "topic": "生酮饮食与糖尿病", "keywords": ["ketogenic diet diabetes type 2", "keto diet blood glucose HbA1c"]},
    {"group": "糖尿病患者", "topic": "间歇性断食与糖尿病", "keywords": ["intermittent fasting diabetes outcomes", "time restricted eating blood glucose"]},
    {"group": "糖尿病患者", "topic": "糖尿病微量元素需求", "keywords": ["diabetes chromium magnesium zinc", "trace elements diabetes glucose metabolism"]},
    {"group": "糖尿病患者", "topic": "糖尿病肾病饮食管理", "keywords": ["diabetic nephropathy diet protein restriction", "diabetes kidney disease nutrition management"]},
    {"group": "糖尿病患者", "topic": "糖尿病足与营养支持", "keywords": ["diabetic foot ulcer nutrition wound healing", "diabetes wound care nutritional support"]},

    # ========== 7. 通用主题（80张目标）==========
    {"group": "通用", "topic": "蛋白质需求与优质蛋白来源", "keywords": ["protein requirements adults dietary reference", "high quality protein sources amino acid"]},
    {"group": "通用", "topic": "碳水化合物质量与健康", "keywords": ["carbohydrate quality glycemic health", "whole grains refined carbs disease risk"]},
    {"group": "通用", "topic": "膳食脂肪类型与心血管健康", "keywords": ["dietary fat types cardiovascular disease", "saturated unsaturated fat heart health"]},
    {"group": "通用", "topic": "维生素D缺乏与补充", "keywords": ["vitamin D deficiency prevalence supplementation", "vitamin D bone immune health"]},
    {"group": "通用", "topic": "B族维生素与健康", "keywords": ["B vitamins health deficiency", "thiamine riboflavin niacin folate B12"]},
    {"group": "通用", "topic": "矿物质钙铁锌硒", "keywords": ["essential minerals calcium iron zinc selenium", "mineral deficiency dietary sources"]},
    {"group": "通用", "topic": "抗氧化物质与慢性病预防", "keywords": ["antioxidants chronic disease prevention", "polyphenols flavonoids health benefits"]},
    {"group": "通用", "topic": "食物烹饪方式与营养保留", "keywords": ["cooking methods nutrient retention", "food preparation vitamin loss"]},
    {"group": "通用", "topic": "食品添加剂安全性与法规", "keywords": ["food additives safety regulations", "preservatives colorants health effects"]},
    {"group": "通用", "topic": "饮食模式与长寿", "keywords": ["dietary patterns longevity Blue Zones", "healthy aging diet life expectancy"]},

    # ========== 补充子主题（扩充至500+张）==========
    # 普通人补充
    {"group": "普通人", "topic": "钠摄入与健康", "keywords": ["sodium intake health adults", "salt reduction blood pressure population"]},
    {"group": "普通人", "topic": "糖摄入与代谢健康", "keywords": ["sugar intake metabolic health", "added sugars chronic disease risk"]},
    {"group": "普通人", "topic": "咖啡与健康", "keywords": ["coffee consumption health outcomes", "caffeine intake chronic disease"]},
    # 健身用户补充
    {"group": "健身用户", "topic": "碳水加载与耐力表现", "keywords": ["carbohydrate loading endurance performance", "carb loading marathon glycogen"]},
    {"group": "健身用户", "topic": "β-丙氨酸与运动表现", "keywords": ["beta alanine exercise performance", "carnosine supplement muscular endurance"]},
    # 孕妇补充
    {"group": "孕妇", "topic": "孕期益生菌与肠道健康", "keywords": ["probiotics pregnancy gut health", "pregnancy microbiome probiotic supplementation"]},
    {"group": "孕妇", "topic": "孕期维生素A与胎儿发育", "keywords": ["vitamin A pregnancy fetal development", "retinol pregnancy toxicity safe intake"]},
    # 青少年补充
    {"group": "青少年", "topic": "青少年碘营养与甲状腺", "keywords": ["iodine deficiency adolescents thyroid", "teenager iodine nutrition cognitive"]},
    {"group": "青少年", "topic": "青少年零食选择与营养", "keywords": ["adolescent snacking nutrition quality", "healthy snacks teenagers dietary"]},
    # 老年人补充
    {"group": "老年人", "topic": "老年肌肉合成与亮氨酸", "keywords": ["leucine muscle protein synthesis elderly", "elderly leucine supplementation sarcopenia"]},
    {"group": "老年人", "topic": "老年ω-3脂肪酸与认知", "keywords": ["omega-3 fatty acids cognitive elderly", "fish oil aging brain health"]},
    # 糖尿病患者补充
    {"group": "糖尿病患者", "topic": "糖尿病与ω-3脂肪酸", "keywords": ["omega-3 diabetes cardiovascular", "fish oil diabetic patients outcomes"]},
    {"group": "糖尿病患者", "topic": "糖尿病与酒精摄入", "keywords": ["alcohol diabetes blood glucose risk", "diabetic patients alcohol consumption guidelines"]},
    # 通用补充
    {"group": "通用", "topic": "益生菌与肠道健康", "keywords": ["probiotics gut health microbiome", "probiotic supplementation digestive health"]},
    {"group": "通用", "topic": "植物化学物与健康", "keywords": ["phytochemicals health benefits disease", "plant compounds polyphenols flavonoids"]},
    {"group": "通用", "topic": "食物过敏与不耐受", "keywords": ["food allergy intolerance prevalence", "lactose gluten allergy management"]},
    {"group": "通用", "topic": "营养标签与食品选择", "keywords": ["nutrition label food choice consumer", "front of pack labeling health"]},
]


# ======================== 官方指南数据库（扩充版） ========================
GUIDELINES_DB = [
    # 通用指南
    {"id": "GUIDE_DG2022", "source": "中国居民膳食指南2022", "relevance": ["通用"],
     "key_points": ["食物多样，合理搭配，每天12种以上食物", "多吃蔬果、奶类、全谷、大豆，蔬菜300-500g/天",
                    "适量吃鱼禽蛋瘦肉，每周至少2次鱼", "少盐少油控糖限酒，食盐<5g/天",
                    "规律进餐足量饮水，饮水1500-1700ml/天", "会烹会选会看标签"]},
    {"id": "GUIDE_WHO_DIET", "source": "WHO健康饮食建议", "relevance": ["通用"],
     "key_points": ["每天至少400g水果和蔬菜", "主食以全谷物和根茎类为主",
                    "限制脂肪摄入，优选健康脂肪", "盐<5g/天，糖<25g/天",
                    "避免工业反式脂肪"]},
    {"id": "GUIDE_WHO_NUTRI", "source": "WHO全球营养报告", "relevance": ["通用"],
     "key_points": ["全球1/3成年人超重或肥胖", "不健康饮食每年致1100万人死亡",
                    "建议多样化饮食，增加果蔬", "限制饱和脂肪、反式脂肪、糖和盐"]},
    # 糖尿病
    {"id": "GUIDE_DIABETES2023", "source": "中国营养学会-糖尿病食养指南2023", "relevance": ["糖尿病患者", "通用"],
     "key_points": ["糖尿病每日主食200-300g", "优先低GI食物：燕麦、糙米、全麦",
                    "膳食纤维25-30g/天", "添加糖<25g/天", "定时定量进餐", "餐后血糖<10mmol/L"]},
    {"id": "GUIDE_ADA_2024", "source": "美国糖尿病协会ADA营养指南2024", "relevance": ["糖尿病患者"],
     "key_points": ["个性化饮食计划", "碳水45-60%，强调复杂碳水", "膳食纤维改善血糖",
                    "饱和脂肪<7%总热量", "钠<2300mg/天", "酒精需谨慎"]},
    # 高血压
    {"id": "GUIDE_HYPERTENSION", "source": "中国营养学会-高血压食养指南2023", "relevance": ["老年人", "通用"],
     "key_points": ["食盐<5g/天", "增加钾摄入，多吃果蔬", "限制饮酒",
                    "BMI维持18.5-23.9", "每周150分钟中等强度运动"]},
    # 高血脂
    {"id": "GUIDE_BLOODLIPID", "source": "中国营养学会-血脂异常食养指南2023", "relevance": ["老年人", "通用"],
     "key_points": ["总脂肪<30%总热量", "饱和脂肪<10%总热量", "增加不饱和脂肪酸",
                    "膳食纤维25-30g/天", "限制精制碳水", "戒烟限酒"]},
    # 肥胖
    {"id": "GUIDE_OVERWEIGHT", "source": "中国营养学会-肥胖食养指南2024", "relevance": ["普通人", "通用"],
     "key_points": ["每日热量减少300-500kcal", "保证蛋白质摄入", "增加膳食纤维",
                    "减少精制碳水和高脂食物", "规律运动配合", "避免极端节食"]},
    # 孕妇
    {"id": "GUIDE_PREGNANT", "source": "中国营养学会-孕期妇女膳食指南", "relevance": ["孕妇"],
     "key_points": ["孕早期叶酸400μg/天", "孕中晚期蛋白质增加15-30g/天",
                    "钙1000-1200mg/天，铁24-29mg/天", "每周2-3次深海鱼补充DHA",
                    "避免生食、未灭菌乳制品", "孕中晚期每周增重0.3-0.5kg"]},
    {"id": "GUIDE_WHO_PREGNANT", "source": "WHO孕期营养建议", "relevance": ["孕妇"],
     "key_points": ["每日补充30-60mg铁+400μg叶酸", "钙不足地区每日补充1.5-2g钙",
                    "避免酒精、烟草、高汞鱼", "适量体育活动有益", "体重增长个体化管理"]},
    # 老年人
    {"id": "GUIDE_ELDERLY", "source": "中国营养学会-老年人膳食指南", "relevance": ["老年人"],
     "key_points": ["蛋白质1.0-1.2g/kg体重/天", "增加优质蛋白：鱼禽蛋奶大豆",
                    "钙1000mg/天，维生素D 15μg/天", "少量多餐，食物细软",
                    "预防肌少症，适度抗阻运动", "每日饮水1500-1700ml"]},
    # 青少年
    {"id": "GUIDE_ADOLESCENT", "source": "中国营养学会-儿童青少年膳食指南", "relevance": ["青少年"],
     "key_points": ["钙1000-1200mg/天", "保证早餐，三餐规律", "蛋白质55-75g/天",
                    "限制含糖饮料和零食", "每周60分钟中高强度运动", "睡眠8-10小时"]},
    # 健身
    {"id": "GUIDE_ISSN", "source": "国际运动营养学会ISSN立场声明", "relevance": ["健身用户"],
     "key_points": ["力量训练蛋白质1.6-2.2g/kg/天", "运动后30分钟内补充20-40g优质蛋白",
                    "碳水3-5g/kg/天维持训练强度", "肌酸3-5g/天提升力量",
                    "每日饮水35-40ml/kg", "以天然食物为主"]},
    {"id": "GUIDE_ACSM", "source": "美国运动医学会ACSM运动营养指南", "relevance": ["健身用户"],
     "key_points": ["耐力运动员碳水6-10g/kg/天", "耐力蛋白质1.2-1.4g/kg/天",
                    "力量蛋白质1.6-1.7g/kg/天", "运动前2-4小时碳水1-4g/kg",
                    "长时间运动补充电解质", "恢复期碳水:蛋白=3:1-4:1"]},
    # 哺乳期
    {"id": "GUIDE_LACTATION", "source": "中国营养学会-哺乳期妇女膳食指南", "relevance": ["孕妇"],
     "key_points": ["哺乳期每日增加500kcal热量", "蛋白质增加25g/天",
                    "继续补充叶酸和DHA", "多喝汤水促进泌乳", "避免酒精和咖啡因过量"]},
    # 维生素D
    {"id": "GUIDE_VITD", "source": "中华医学会-维生素D缺乏防治共识", "relevance": ["通用", "老年人", "青少年", "孕妇"],
     "url": "http://www.cma.org.cn/",
     "key_points": ["成人维生素D推荐400-600IU/天", "缺乏人群可补充800-2000IU/天",
                    "日照是主要来源，每日15-30分钟", "缺乏与骨质疏松、免疫下降相关",
                    "孕妇和老年人更需关注维生素D状态"]},
]


# ======================== Token 追踪器 ========================
class TokenTracker:
    def __init__(self):
        self.total_input = 0
        self.total_output = 0
        self.calls = 0
    def add(self, usage):
        self.total_input += usage.get("prompt_tokens", 0)
        self.total_output += usage.get("completion_tokens", 0)
        self.calls += 1
    @property
    def total(self):
        return self.total_input + self.total_output


# ======================== DeepSeek 调用 ========================
def call_deepseek(prompt, tracker, system="你是专业的知识库构建专家。",
                  temperature=0.2, max_tokens=400):
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": DEEPSEEK_MODEL,
               "messages": [{"role": "system", "content": system},
                           {"role": "user", "content": prompt}],
               "temperature": temperature, "max_tokens": max_tokens}
    for attempt in range(3):
        try:
            resp = requests.post(f"{DEEPSEEK_API_BASE}/chat/completions",
                               headers=headers, json=payload, timeout=120)
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            tracker.add(data.get("usage", {}))
            return content
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
            else:
                print(f"    ✗ API调用失败：{e}")
                return None


# ======================== PubMed 搜索 ========================
def search_pubmed(keyword, max_results=4):
    try:
        resp = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                          params={"db": "pubmed", "term": keyword, "retmax": max_results,
                                  "retmode": "json", "sort": "relevance"}, timeout=15)
        pmids = resp.json().get("esearchresult", {}).get("idlist", [])
        if not pmids:
            return []
        results = []
        for pmid in pmids:
            try:
                sresp = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                                   params={"db": "pubmed", "id": pmid, "retmode": "json"}, timeout=15)
                article = sresp.json().get("result", {}).get(pmid, {})
                title = article.get("title", "")
                journal = article.get("fulljournalname", "")
                pubdate = article.get("pubdate", "")[:4]
                authors_list = article.get("authors", [])
                authors = ", ".join([a.get("name", "") for a in authors_list[:3]])
                abstract = ""
                try:
                    from bs4 import BeautifulSoup
                    fresp = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                                        params={"db": "pubmed", "id": pmid, "retmode": "xml", "rettype": "abstract"},
                                        timeout=15)
                    soup = BeautifulSoup(fresp.text, "xml")
                    abstract_elem = soup.find("Abstract")
                    if abstract_elem:
                        abstract = " ".join([t.get_text(strip=True) for t in abstract_elem.find_all("AbstractText")])
                except:
                    pass
                if title:
                    results.append({
                        "id": f"PMID_{pmid}", "source_channel": "PubMed",
                        "title": title, "authors": authors, "journal": journal,
                        "pubdate": pubdate,
                        "content": abstract[:800] if abstract else f"研究关于{title}的相关内容",
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                    })
                time.sleep(0.4)
            except:
                continue
        return results
    except:
        return []


# ======================== 官方指南匹配 ========================
def get_guidelines_for_group(group):
    matched = []
    for g in GUIDELINES_DB:
        if group in g["relevance"] or "通用" in g["relevance"]:
            content = f"【{g['source']}核心建议】\n"
            for kp in g["key_points"]:
                content += f"- {kp}\n"
            matched.append({
                "id": g["id"], "source_channel": "官方指南",
                "title": g["source"], "authors": "权威机构",
                "journal": g["source"], "pubdate": "2023-2024",
                "content": content, "url": g.get("url", ""),
                "is_official_guide": True
            })
    return matched


# ======================== 知识卡片提纯 ========================
def purify_material(mat, group, topic, tracker):
    purify_prompt = f"""你是知识库构建专家。请从以下文献中提取4类核心信息，输出结构化知识卡片（150-250字）。

【文献来源】来源渠道：{mat.get('source_channel', '未知')} | 标题：{mat.get('title', '')}
【适用主题】{group} - {topic}

【文献内容】
{mat.get('content', '')[:1000]}

【提取规则】
1. 仅提取：核心循证结论、量化临床数据、适用人群、局限性/学术争议
2. 150-250字，极简结构化
3. 过滤动物实验、非人体临床内容
4. 严格按格式输出：

【核心循证结论】[1-2句]
【量化临床数据】[数值或"暂无"]
【适用人群】[明确人群]
【局限性/学术争议】[局限或争议]"""

    purified = call_deepseek(purify_prompt, tracker, max_tokens=400)
    if not purified:
        return None
    
    return {
        "card_id": mat.get("id", ""),
        "title": mat.get("title", ""),
        "group": group,
        "topic": topic,
        "source_channel": mat.get("source_channel", "未知"),
        "source_url": mat.get("url", ""),
        "authors": mat.get("authors", ""),
        "journal": mat.get("journal", ""),
        "pubdate": mat.get("pubdate", ""),
        "purified_content": purified,
        "is_official_guide": mat.get("is_official_guide", False),
        "ingest_time": datetime.now().isoformat(),
        "version": 1
    }


# ======================== 分层去重 + 智能合并 ========================
def deduplicate_and_merge(new_card, existing_cards):
    """
    返回: ("drop", None) - ID重复，丢弃
         ("add", None) - 新内容，直接添加
         ("merge", merged_card) - 合并到现有卡片
    """
    # 第一层：ID硬去重
    for card in existing_cards:
        if card["card_id"] == new_card["card_id"] and new_card["card_id"]:
            return ("drop", None)
    
    # 第二层：标题相似度评估
    for i, card in enumerate(existing_cards):
        sim = title_similarity(card["title"], new_card["title"])
        if sim >= 0.8:
            # 第三层：结论一致性判断（简单版 - 基于内容关键词）
            if conclusions_consistent(card["purified_content"], new_card["purified_content"]):
                # 结论一致 → 合并
                merged = merge_cards(card, new_card)
                return ("merge", (i, merged))
            else:
                # 结论可能相反 → 都保留，标记争议关联
                new_card["debate_relation"] = {
                    "related_card_id": card["card_id"],
                    "relation_type": "potential_contradictory",
                    "note": "标题相似但结论可能不同，保留为争议关联"
                }
                return ("add", None)
    
    return ("add", None)


def title_similarity(t1, t2):
    """标题相似度计算（基于字符重叠率）"""
    t1, t2 = t1.lower(), t2.lower()
    if not t1 or not t2:
        return 0.0
    # 提取关键词
    words1 = set(re.findall(r'[a-z\u4e00-\u9fff]{3,}', t1))
    words2 = set(re.findall(r'[a-z\u4e00-\u9fff]{3,}', t2))
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union)


def conclusions_consistent(c1, c2):
    """判断两个结论是否一致（简单版：基于关键结论行比对）"""
    # 提取核心结论部分
    def extract_conclusion(text):
        match = re.search(r'【核心循证结论】(.+?)(?=【|$)', text, re.S)
        return match.group(1).strip() if match else text[:100]
    
    concl1 = extract_conclusion(c1)
    concl2 = extract_conclusion(c2)
    
    # 检查是否包含相反关键词
    opposite_pairs = [("增加", "降低"), ("升高", "降低"), ("有益", "有害"),
                      ("改善", "恶化"), ("positive", "negative"), ("increase", "decrease")]
    for w1, w2 in opposite_pairs:
        if (w1 in concl1 and w2 in concl2) or (w2 in concl1 and w1 in concl2):
            return False  # 可能相反
    return True  # 默认一致


def merge_cards(card1, card2):
    """合并两张知识卡片"""
    merged = card1.copy()
    merged["purified_content"] = card1["purified_content"] + "\n\n" + card2["purified_content"]
    merged["merged_from"] = [
        {"id": card1["card_id"], "title": card1["title"]},
        {"id": card2["card_id"], "title": card2["title"]}
    ]
    merged["card_id"] = f"MERGED_{card1['card_id']}_{card2['card_id']}"
    merged["version"] = card1.get("version", 1) + 1
    merged["merge_time"] = datetime.now().isoformat()
    return merged


# ======================== 进度管理 ========================
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"completed_subtopics": [], "cards": []}


def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def load_kb():
    if os.path.exists(KB_FILE):
        with open(KB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_kb(cards):
    with open(KB_FILE, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)


# ======================== 主流程 ========================
def main():
    print("=" * 70)
    print("全人群知识库批量构建")
    print(f"目标：{TARGET_CARDS}张卡片")
    print(f"子主题数：{len(SUBTOPICS_CONFIG)}")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    tracker = TokenTracker()
    progress = load_progress()
    existing_cards = progress["cards"]
    completed = set(progress["completed_subtopics"])
    
    print(f"已有卡片：{len(existing_cards)}张")
    print(f"已完成子主题：{len(completed)}/{len(SUBTOPICS_CONFIG)}")
    
    for idx, subtopic in enumerate(SUBTOPICS_CONFIG):
        topic_key = f"{subtopic['group']}_{subtopic['topic']}"
        
        if topic_key in completed:
            print(f"\n[{idx+1}/{len(SUBTOPICS_CONFIG)}] 跳过已完成：{topic_key}")
            continue
        
        if len(existing_cards) >= TARGET_CARDS:
            print(f"\n已达到目标卡片数 {TARGET_CARDS}，停止构建")
            break
        
        print(f"\n[{idx+1}/{len(SUBTOPICS_CONFIG)}] 处理：{topic_key}")
        print(f"  当前卡片总数：{len(existing_cards)}")
        
        # PubMed搜索
        all_materials = []
        for kw in subtopic["keywords"]:
            print(f"  [PubMed] {kw}")
            results = search_pubmed(kw, max_results=4)
            all_materials.extend(results)
            time.sleep(0.5)
        
        # 官方指南
        guides = get_guidelines_for_group(subtopic["group"])
        all_materials.extend(guides)
        print(f"  素材汇总：PubMed {len(all_materials) - len(guides)}篇 + 指南 {len(guides)}篇 = {len(all_materials)}篇")
        
        # 提纯 + 去重 + 合并
        new_count = 0
        for mat in all_materials:
            card = purify_material(mat, subtopic["group"], subtopic["topic"], tracker)
            if not card:
                continue
            
            action, result = deduplicate_and_merge(card, existing_cards)
            if action == "drop":
                print(f"    ✗ 去重丢弃：{card['card_id']}")
            elif action == "add":
                existing_cards.append(card)
                new_count += 1
            elif action == "merge":
                i, merged = result
                existing_cards[i] = merged
                print(f"    ↔ 合并卡片：{card['card_id']} → {existing_cards[i]['card_id']}")
        
        print(f"  新增卡片：{new_count}张，当前总数：{len(existing_cards)}")
        
        # 保存进度
        completed.add(topic_key)
        progress["completed_subtopics"] = list(completed)
        progress["cards"] = existing_cards
        save_progress(progress)
        
        # 打印Token消耗
        print(f"  Token累计：{tracker.total}（调用{tracker.calls}次）")
    
    # 最终保存
    save_kb(existing_cards)
    
    # 统计
    print(f"\n{'='*70}")
    print("知识库构建完成")
    print(f"{'='*70}")
    print(f"总卡片数：{len(existing_cards)}")
    print(f"总Token消耗：{tracker.total}")
    print(f"API调用次数：{tracker.calls}")
    
    # 按人群统计
    group_stats = {}
    for card in existing_cards:
        g = card.get("group", "未知")
        group_stats[g] = group_stats.get(g, 0) + 1
    
    print(f"\n各人群卡片数：")
    for g, count in sorted(group_stats.items()):
        print(f"  {g}: {count}张")
    
    print(f"\n知识库已保存至：{KB_FILE}")


if __name__ == "__main__":
    main()
