#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
食材数据精简合并脚本 v9 - 最终版
策略：原始数据过滤+智能分类+积极合并
目标：380-450条
"""
import os
import csv
import re
from collections import defaultdict

INPUT_CSV = r"C:\Users\13425\Desktop\个人健康助手\health\ai_service\test_output\food_data_review\china_food_simplified.csv"
OUTPUT_CSV = r"C:\Users\13425\Desktop\个人健康助手\health\ai_service\test_output\food_data_review\food_data_final.csv"

DISPLAY_RULES = {
    "奶类":    (True, False, False),
    "水果":    (True, False, False),
    "主食":    (True, False, False),
    "蔬菜":    (True, True, False),
    "豆制品":  (True, True, False),
    "水产":    (False, True, True),
    "肉蛋类":  (False, False, False),
    "油脂类":  (False, False, False),
}

CATEGORY_ORDER = ["奶类", "肉蛋类", "水产", "主食", "豆制品", "蔬菜", "水果", "油脂类"]

# 明确分类映射 - 基于食材名称而非原始分类
CATEGORY_MAP = {
    # 奶类
    "牛奶": "奶类", "酸奶": "奶类", "奶酪": "奶类", "奶粉": "奶类",
    "奶油": "奶类", "炼乳": "奶类", "黄油": "奶类", "羊奶": "奶类",
    # 肉蛋类
    "猪": "肉蛋类", "牛": "肉蛋类", "羊": "肉蛋类", "鸡": "肉蛋类",
    "鸭": "肉蛋类", "鹅": "肉蛋类", "鸽": "肉蛋类", "蛋": "肉蛋类",
    # 水产
    "鱼": "水产", "虾": "水产", "蟹": "水产", "贝": "水产",
    "蚌": "水产", "螺": "水产", "乌贼": "水产", "鱿": "水产",
    "章鱼": "水产", "海": "水产", "河": "水产",
    # 主食
    "米": "主食", "面": "主食", "粉": "主食", "馒头": "主食",
    "面条": "主食", "饼": "主食", "饺": "主食", "包": "主食",
    "饭": "主食", "粥": "主食", "玉米": "主食", "红薯": "主食",
    "土豆": "主食", "山药": "主食", "芋": "主食", "薏苡": "主食",
    "燕麦": "主食", "莜麦": "主食", "荞麦": "主食", "糜子": "主食",
    "黍": "主食", "稷": "主食", "高粱": "主食", "青稞": "主食",
    # 豆制品
    "豆腐": "豆制品", "豆干": "豆制品", "腐竹": "豆制品",
    "豆浆": "豆制品", "豆皮": "豆制品", "豆奶": "豆制品",
    "黄豆": "豆制品", "绿豆": "豆制品", "红豆": "豆制品",
    "黑豆": "豆制品", "青豆": "豆制品", "豆芽": "豆制品",
    "素鸡": "豆制品", "素肠": "豆制品", "素鸭": "豆制品",
    # 蔬菜
    "白菜": "蔬菜", "菠菜": "蔬菜", "芹菜": "蔬菜", "西红柿": "蔬菜",
    "番茄": "蔬菜", "黄瓜": "蔬菜", "茄子": "蔬菜", "青椒": "蔬菜",
    "辣椒": "蔬菜", "胡萝卜": "蔬菜", "白萝卜": "蔬菜", "萝卜": "蔬菜",
    "藕": "蔬菜", "韭菜": "蔬菜", "生菜": "蔬菜", "油菜": "蔬菜",
    "菠菜": "蔬菜", "油麦菜": "蔬菜", "苦菊": "蔬菜", "茼蒿": "蔬菜",
    "芥菜": "蔬菜", "豆角": "蔬菜", "豇豆": "蔬菜", "四季豆": "蔬菜",
    "扁豆": "蔬菜", "南瓜": "蔬菜", "冬瓜": "蔬菜", "丝瓜": "蔬菜",
    "苦瓜": "蔬菜", "佛手瓜": "蔬菜", "西葫芦": "蔬菜",
    "蘑菇": "蔬菜", "香菇": "蔬菜", "金针菇": "蔬菜", "木耳": "蔬菜",
    "杏鲍菇": "蔬菜", "茶树菇": "蔬菜", "口蘑": "蔬菜",
    "牛肝菌": "蔬菜", "牛眼睛菌": "蔬菜",
    "洋葱": "蔬菜", "大蒜": "蔬菜", "姜": "蔬菜", "葱": "蔬菜",
    "海带": "蔬菜", "紫菜": "蔬菜", "裙带菜": "蔬菜",
    "芦笋": "蔬菜", "西兰花": "蔬菜", "菜花": "蔬菜", "花菜": "蔬菜",
    "香菜": "蔬菜", "薄荷": "蔬菜", "紫苏": "蔬菜", "香椿": "蔬菜",
    "豌豆": "蔬菜", "蚕豆": "蔬菜", "荷兰豆": "蔬菜",
    # 水果
    "苹果": "水果", "香蕉": "水果", "橙": "水果", "橘": "水果",
    "桔": "水果", "葡萄": "水果", "梨": "水果", "鸭梨": "水果",
    "鹅黄梨": "水果", "鸭广梨": "水果", "雪梨": "水果", "山梨": "水果",
    "西瓜": "水果", "哈密瓜": "水果", "甜瓜": "水果", "草莓": "水果",
    "蓝莓": "水果", "芒果": "水果", "菠萝": "水果", "桃": "水果",
    "樱桃": "水果", "李子": "水果", "杏子": "水果", "猕猴桃": "水果",
    "柚子": "水果", "柠檬": "水果", "山楂": "水果", "枣": "水果",
    "荔枝": "水果", "龙眼": "水果", "火龙果": "水果", "枇杷": "水果",
    "柿子": "水果", "石榴": "水果", "无花果": "水果", "椰子": "水果",
    "榴莲": "水果", "蟠桃": "水果", "猕猴桃": "水果",
    # 油脂类
    "花生油": "油脂类", "大豆油": "油脂类", "菜籽油": "油脂类",
    "玉米油": "油脂类", "橄榄油": "油脂类", "猪油": "油脂类",
    "牛油": "油脂类", "羊油": "油脂类", "芝麻油": "油脂类",
    "茶油": "油脂类", "椰子油": "油脂类", "米糠油": "油脂类",
    "棉籽油": "油脂类", "亚麻籽油": "油脂类", "黄油": "油脂类",
}

# 过滤关键词 - 仅过滤明显的加工复合食品
FILTER_KEYWORDS = [
    "预制菜", "速冻水饺", "速冻包子",
    "蛋糕", "饼干", "面包(加工)",
    "麻辣烫", "火锅底料",
    "饮料", "饮品",
    "糖果", "巧克力", "冰淇淋",
    "辣条", "薯片", "方便面(加工)",
    "人乳", "人奶", "母乳",
    "驼奶", "驼乳", "鲜驼奶",
    "酥油茶",
    "狗肉", "猫肉", "狐狸肉",
    "凤爪(加工)", "泡椒凤爪",
]

# 分类内排序 - 按日常使用频率，高频在前
FREQUENCY_ORDER = {
    "奶类": [
        "牛奶", "低脂奶", "脱脂奶", "酸奶", "奶酪",
        "奶粉", "炼乳", "奶油", "黄油",
        "羊奶", "豆奶",
    ],
    "肉蛋类": [
        "猪肉", "牛肉", "羊肉", "鸡肉", "鸭肉",
        "鸡蛋", "鸭蛋", "鹌鹑蛋",
        "猪肝",
        "午餐肉", "腊肉", "腊肠", "火腿", "香肠",
    ],
    "水产": [
        "草鱼", "带鱼", "鲤鱼", "鲫鱼", "黄花鱼",
        "三文鱼", "虾", "蟹", "贝类",
        "鲈鱼", "鲅鱼", "黄鳝", "泥鳅", "甲鱼",
        "墨鱼", "鱿鱼",
    ],
    "主食": [
        "大米", "小米", "面粉", "糙米", "糯米",
        "燕麦", "红薯", "土豆", "玉米",
        "馒头", "面条", "米饭", "小米粥",
        "荞麦", "薏米", "高粱米",
    ],
    "豆制品": [
        "豆腐", "豆腐脑", "腐竹", "豆腐干",
        "豆浆", "黄豆", "绿豆", "红豆", "黑豆", "豆芽",
    ],
    "蔬菜": [
        "白菜", "菠菜", "芹菜", "西红柿", "黄瓜",
        "茄子", "青椒", "胡萝卜", "白萝卜", "藕",
        "韭菜", "生菜", "豆角", "南瓜", "冬瓜",
        "丝瓜", "苦瓜", "蘑菇", "香菇", "木耳",
        "洋葱", "大蒜", "姜", "油菜", "油麦菜",
        "海带", "紫菜", "西兰花", "菜花", "香菜",
        "豌豆", "蚕豆",
    ],
    "水果": [
        "苹果", "香蕉", "橙子", "葡萄", "梨",
        "西瓜", "草莓", "芒果", "菠萝", "桃",
        "樱桃", "猕猴桃", "柚子", "柠檬", "枣",
        "荔枝", "龙眼", "枇杷", "柿子", "石榴",
    ],
    "油脂类": [
        "花生油", "大豆油", "菜籽油", "玉米油",
        "橄榄油", "猪油", "芝麻油", "茶油",
    ],
}

# 稀有食材过滤 - 仅过滤极少见的野生/ exotic食材
RARE_FOODS = [
    "玻璃草", "大蓟", "小旋花", "山苦荬", "扁蓄",
    "朝鲜蓟", "松蘑", "根芹",
    "梧桐", "榆钱", "槐花(野)", "沙参", "沙蓬", "清明菜",
    "大薯", "打碗花", "苦荬", "马齿苋(野生)", "蕨菜(野生)",
    "马兰", "车前草", "鱼腥草(野生)",
    "三七尖", "土三七", "地肤", "地衣", "夏枯草", "大巢菜",
    "大红菇", "灰灰菜", "爬景天", "牛蒡叶",
    "独行菜", "猴头菇(野生)", "玉兰片", "珍珠白蘑",
    "球茎茴香", "琼脂", "瓢儿白", "甜脆荷兰豆",
    "番杏", "白凤菜", "白沙蒿",
    "牛肝菌(野生)", "乳牛肝菌", "元蘑", "北风菌",
    "刀豆(野生)", "刺五加", "刺儿菜", "卞萝卜",
    "发芽豆", "发菜", "叶甜菜", "垄船豆",
    "骆驼", "驴", "火鸡", "马(食用)",
    "蛤蚧", "刺猬",
    "蟾蜍", "蛤蟆",
    "鱼翅", "干贝(稀有)", "瑶柱",
    "鱼肚", "鱼唇", "裙边",
    "余柑子", "吊蛋", "子瓜",
    "布朗(稀有)", "早橘",
    "杏干(药用)", "杨桃(野生)", "百香果(野生)",
    "牛油果(野生)", "蛇果", "莲雾(稀有)",
    "蒲菜", "蒌蒿", "薤", "蛹虫草", "螺旋藻",
    "血红菇", "观达菜", "豆瓣菜", "豆薯",
    "败酱", "软化白菊苣", "达乌里胡枝子", "酢浆草",
    "酸模", "野苋菜(野生)", "野菊", "金瓜(野生)",
    "金针菜(野生)", "青头菌", "青萝卜(野生)",
    "飞碟瓜", "食用大黄", "食用黄麻", "香杏丁蘑",
    "香瓜茄", "香茅", "麦瓶草",
    "黄伞菇", "黄茎瓜", "黄麻叶",
    "龙牙豆", "龙豆", "胡芦条",
    "木香", "葛(野生)", "葫子",
]

# 合并映射
MERGE_MAP = {
    "牛奶": ["纯牛奶", "全脂牛奶", "鲜牛奶", "纯牛乳", "牛奶"],
    "低脂奶": ["低脂牛奶", "低脂奶", "部分脱脂牛奶", "低脂纯牛奶"],
    "脱脂奶": ["脱脂牛奶", "脱脂奶", "无脂牛奶", "脱脂纯牛奶"],
    "酸奶": ["酸奶", "酸牛乳", "发酵乳"],
    "奶酪": ["奶酪", "干酪", "芝士", "乳酪"],
    "奶粉": ["奶粉", "全脂奶粉", "脱脂奶粉", "乳粉"],
    "奶油": ["奶油", "淡奶油", "稀奶油"],
    "炼乳": ["炼乳", "浓缩乳"],
    "豆奶": ["豆奶", "豆乳饮料"],
    "羊奶": ["羊奶", "羊乳"],
    
    "猪肉": ["猪肉", "猪瘦肉", "里脊肉", "五花肉", "猪后腿", "排骨"],
    "牛肉": ["牛肉", "牛瘦肉", "牛里脊", "牛腩"],
    "羊肉": ["羊肉", "羊腿"],
    "鸡肉": ["鸡肉", "土鸡"],
    "鸭肉": ["鸭肉", "鸭"],
    "鸡蛋": ["鸡蛋", "鲜鸡蛋"],
    "鸭蛋": ["鸭蛋"],
    "鹌鹑蛋": ["鹌鹑蛋"],
    "猪肝": ["猪肝"],
    "肉松": ["肉松", "鸡肉松", "猪肉松", "牛肉松"],
    
    "草鱼": ["草鱼", "白鲩"],
    "带鱼": ["带鱼"],
    "黄花鱼": ["黄花鱼", "大黄鱼", "小黄鱼"],
    "鲤鱼": ["鲤鱼"],
    "鲫鱼": ["鲫鱼"],
    "三文鱼": ["三文鱼", "鲑鱼"],
    "虾": ["虾", "河虾", "对虾", "基围虾"],
    "蟹": ["蟹", "螃蟹", "青蟹", "梭子蟹"],
    "贝类": ["贝", "扇贝", "生蚝", "牡蛎", "花蛤"],
    "墨鱼": ["墨鱼", "乌贼"],
    "鲈鱼": ["鲈鱼"],
    "鲅鱼": ["鲅鱼", "马鲛鱼"],
    "黄鳝": ["黄鳝", "鳝鱼"],
    "泥鳅": ["泥鳅"],
    "甲鱼": ["甲鱼", "鳖"],
    "河蚌": ["河蚌"],
    "金枪鱼": ["金枪鱼"],
    "鳕鱼": ["鳕鱼"],
    
    "大米": ["大米", "粳米", "籼米"],
    "小米": ["小米", "粟米"],
    "面粉": ["面粉", "小麦粉"],
    "糙米": ["糙米"],
    "糯米": ["糯米", "江米"],
    "燕麦": ["燕麦", "莜麦"],
    "红薯": ["红薯", "甘薯", "地瓜"],
    "土豆": ["土豆", "马铃薯"],
    "玉米": ["玉米", "玉米粒"],
    "小米粥": ["小米粥"],
    "馒头": ["馒头"],
    "面条": ["面条", "挂面"],
    "饺子皮": ["饺子皮"],
    "米饭": ["米饭", "大米饭"],
    "荞麦": ["荞麦", "苦荞麦"],
    "薏米": ["薏米", "薏苡仁"],
    "高粱米": ["高粱米"],
    "青稞": ["青稞"],
    
    "豆腐": ["豆腐", "南豆腐", "北豆腐"],
    "豆腐脑": ["豆腐脑", "豆花"],
    "腐竹": ["腐竹", "豆腐皮"],
    "豆腐干": ["豆腐干", "豆干"],
    "豆浆": ["豆浆", "豆乳"],
    "黄豆": ["黄豆", "大豆"],
    "绿豆": ["绿豆"],
    "红豆": ["红豆", "赤豆"],
    "黑豆": ["黑豆"],
    "豆芽": ["豆芽", "黄豆芽", "绿豆芽"],
    "素鸡": ["素鸡"],
    "芸豆": ["芸豆", "四季豆"],
    
    "白菜": ["白菜", "大白菜", "娃娃菜"],
    "菠菜": ["菠菜"],
    "芹菜": ["芹菜", "西芹"],
    "西红柿": ["西红柿", "番茄"],
    "黄瓜": ["黄瓜", "胡瓜"],
    "茄子": ["茄子"],
    "青椒": ["青椒", "甜椒", "彩椒"],
    "胡萝卜": ["胡萝卜"],
    "白萝卜": ["白萝卜"],
    "藕": ["藕", "莲藕"],
    "韭菜": ["韭菜"],
    "生菜": ["生菜"],
    "豆角": ["豆角", "豇豆", "扁豆"],
    "南瓜": ["南瓜"],
    "冬瓜": ["冬瓜"],
    "丝瓜": ["丝瓜"],
    "苦瓜": ["苦瓜"],
    "蘑菇": ["蘑菇", "口蘑", "平菇"],
    "香菇": ["香菇"],
    "木耳": ["木耳", "黑木耳"],
    "金针菇": ["金针菇"],
    "洋葱": ["洋葱", "葱头"],
    "大蒜": ["大蒜"],
    "姜": ["姜", "生姜"],
    "油菜": ["油菜", "油菜心"],
    "油麦菜": ["油麦菜"],
    "海带": ["海带"],
    "紫菜": ["紫菜"],
    "芦笋": ["芦笋"],
    "西兰花": ["西兰花"],
    "菜花": ["菜花", "花菜"],
    "香菜": ["香菜", "芫荽"],
    "豌豆": ["豌豆"],
    "蚕豆": ["蚕豆"],
    
    "苹果": ["苹果"],
    "香蕉": ["香蕉"],
    "橙子": ["橙子", "桔子", "柑橘"],
    "葡萄": ["葡萄"],
    "梨": ["梨"],
    "西瓜": ["西瓜"],
    "哈密瓜": ["哈密瓜"],
    "草莓": ["草莓"],
    "蓝莓": ["蓝莓"],
    "芒果": ["芒果"],
    "菠萝": ["菠萝"],
    "桃": ["桃", "桃子"],
    "樱桃": ["樱桃"],
    "李子": ["李子"],
    "杏子": ["杏"],
    "猕猴桃": ["猕猴桃", "奇异果"],
    "柚子": ["柚子"],
    "柠檬": ["柠檬"],
    "山楂": ["山楂"],
    "枣": ["枣", "红枣", "大枣"],
    "荔枝": ["荔枝"],
    "龙眼": ["龙眼", "桂圆"],
    "枇杷": ["枇杷"],
    "柿子": ["柿子"],
    "石榴": ["石榴"],
    "无花果": ["无花果"],
    
    "花生油": ["花生油"],
    "大豆油": ["大豆油"],
    "菜籽油": ["菜籽油", "菜油"],
    "玉米油": ["玉米油"],
    "橄榄油": ["橄榄油"],
    "猪油": ["猪油"],
    "芝麻油": ["芝麻油", "香油"],
    "茶油": ["茶油", "山茶油"],
}


def parse_float(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if not val or str(val).strip() in ['', '-', 'None']:
        return None
    try:
        return float(val)
    except:
        return None


def round1(val):
    if val is None:
        return ''
    return round(val, 1)


def get_clean_name(name):
    n = re.sub(r'[（(].*?[）)]', '', name)
    n = re.sub(r'\[.*?\]', '', n)
    n = re.sub(r'\s*$', '', n)
    n = re.sub(r'^\s*', '', n)
    return n.strip()


def should_filter(row):
    name = row['food_name']
    for kw in RARE_FOODS:
        if kw in name:
            return True
    for kw in FILTER_KEYWORDS:
        if kw in name:
            return True
    if row['food_category'] in ['零食']:
        return True
    return False


def fix_category(name, original_cat):
    clean = get_clean_name(name)
    
    if clean == '大米' and original_cat != '主食':
        return original_cat
    
    OIL_SUFFIXES = ['油', '汁', '酱', '酒', '醋', '饮料', '粉']
    
    sorted_keywords = sorted(CATEGORY_MAP.keys(), key=len, reverse=True)
    
    for keyword in sorted_keywords:
        if keyword in clean:
            return CATEGORY_MAP[keyword]
        if clean in keyword:
            if len(clean) < len(keyword):
                for suffix in OIL_SUFFIXES:
                    if keyword.endswith(suffix) and not clean.endswith(suffix):
                        break
                else:
                    return CATEGORY_MAP[keyword]
            elif clean == keyword:
                return CATEGORY_MAP[keyword]
    
    return original_cat


def get_standard_name(name):
    # 否定规则：如果名称包含这些词，跳过某些匹配
    # 格式：(要跳过的别名, 触发跳过的关键词列表)
    NEGATIVE_RULES = [
        ('草莓', ['味', '饮料', '调制乳', '酸奶', '奶粉', '酱']),
        ('桃', ['味', '饮料', '酸奶', '奶粉']),
        ('梨', ['味', '饮料', '酸奶', '奶粉', '糖浆']),
        ('橙', ['味', '饮料', '酸奶', '奶粉']),
        ('橘', ['味', '饮料', '酸奶', '奶粉']),
        ('低脂奶', ['奶粉', '奶酪', '炼乳', '酸奶']),
        ('脱脂奶', ['奶粉', '奶酪', '炼乳', '酸奶']),
        ('全脂牛奶', ['奶粉']),
        ('鸡肉', ['松', '蛋', '血', '肝', '肫', '爪', '翅', '腿', '胸', '皮', '骨', '枞']),
        ('鸭肉', ['松', '蛋', '血', '肝', '肫', '爪', '翅', '腿', '胸', '皮', '骨']),
        ('鸡蛋', ['糕', '卷', '饼', '挞', '羹', '布丁']),
        ('苹果', ['汁', '酱', '酒', '醋', '饮料', '味']),
        ('香蕉', ['汁', '酱', '酒', '醋', '饮料', '味']),
        ('梨', ['汁', '酱', '酒', '醋', '饮料', '味']),
        ('桃', ['汁', '酱', '酒', '醋', '饮料', '味']),
    ]
    
    def check_negative(alias, text):
        for neg_alias, neg_keywords in NEGATIVE_RULES:
            if alias == neg_alias:
                for kw in neg_keywords:
                    if kw in text:
                        return True
        return False
    
    # 第一阶段：在原始名称中查找匹配，优先更长的别名
    candidates = []
    for standard, aliases in MERGE_MAP.items():
        for alias in aliases:
            if alias in name:
                if not check_negative(alias, name):
                    candidates.append((len(alias), standard, alias))
                    break
    
    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    
    # 第二阶段：使用清理后的名称
    clean = get_clean_name(name)
    for standard, aliases in MERGE_MAP.items():
        for alias in aliases:
            if alias in clean or clean in alias:
                if not check_negative(alias, clean):
                    return standard
    
    return clean


def aggregate_rows(rows, category, standard_name):
    display_rule = DISPLAY_RULES.get(category, (False, False, False))
    
    if len(rows) == 1:
        r = rows[0]
        return {
            'food_name': standard_name,
            'alias': '',
            'food_category': category,
            'calorie(kcal/100g)': parse_float(r.get('calorie(kcal/100g)', '')),
            'protein(g/100g)': parse_float(r.get('protein(g/100g)', '')),
            'fat(g/100g)': parse_float(r.get('fat(g/100g)', '')),
            'carb(g/100g)': parse_float(r.get('carb(g/100g)', '')),
            'diet_fiber(g/100g)': parse_float(r.get('diet_fiber(g/100g)', '')),
            'calcium(mg/100g)': parse_float(r.get('calcium(mg/100g)', '')),
            'gi_value': parse_float(r.get('gi_value', '')),
            'folic_acid(μg)': '',
            'dha(mg)': '',
            'show_gi': display_rule[0],
            'show_folic_acid': display_rule[1],
            'show_dha': display_rule[2],
            'remark': '单条',
        }
    
    names = list(set(r['food_name'] for r in rows))
    alias_text = '；'.join(names[:5])
    if len(names) > 5:
        alias_text += f'；等{len(names)}种'
    
    result = {
        'food_name': standard_name,
        'alias': alias_text,
        'food_category': category,
    }
    
    for col in ['calorie(kcal/100g)', 'protein(g/100g)', 'fat(g/100g)',
                'carb(g/100g)', 'diet_fiber(g/100g)', 'calcium(mg/100g)']:
        vals = [parse_float(r.get(col, '')) for r in rows]
        valid = [v for v in vals if v is not None]
        result[col] = sum(valid) / len(valid) if valid else None
    
    gi_vals = [parse_float(r.get('gi_value', '')) for r in rows]
    valid_gi = [v for v in gi_vals if v is not None]
    result['gi_value'] = sum(valid_gi) / len(valid_gi) if valid_gi else None
    
    result['folic_acid(μg)'] = ''
    result['dha(mg)'] = ''
    result['show_gi'] = display_rule[0]
    result['show_folic_acid'] = display_rule[1]
    result['show_dha'] = display_rule[2]
    result['remark'] = f'合并{len(rows)}条均值'
    
    return result


def process():
    with open(INPUT_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
    
    filtered = [r for r in all_rows if not should_filter(r)]
    print(f"原始: {len(all_rows)} 条 → 过滤后: {len(filtered)} 条")
    
    # 修正分类
    for row in filtered:
        row['food_category'] = fix_category(row['food_name'], row['food_category'])
    
    # 标准化名称
    normalized = defaultdict(list)
    for row in filtered:
        cat = row['food_category']
        norm = get_standard_name(row['food_name'])
        normalized[(cat, norm)].append(row)
    
    merged = []
    for (cat, norm), rows in normalized.items():
        result = aggregate_rows(rows, cat, norm)
        cal = result.get('calorie(kcal/100g)')
        if cal is None or cal == 0:
            continue
        merged.append(result)
    
    print(f"标准化合并后: {len(merged)} 条")
    
    # 按分类分组
    category_items = defaultdict(list)
    for item in merged:
        category_items[item['food_category']].append(item)
    
    final_output = []
    id_counter = 1
    
    for cat in CATEGORY_ORDER:
        items = category_items.get(cat, [])
        if not items:
            continue
        
        # 按使用频率排序
        freq_list = FREQUENCY_ORDER.get(cat, [])
        freq_index = {name: i for i, name in enumerate(freq_list)}
        
        def sort_key(item):
            name = item['food_name']
            if name in freq_index:
                return (0, freq_index[name])
            return (1, name)
        
        items.sort(key=sort_key)
        
        final_output.append({
            '__header__': True,
            'text': f"# =====分类：{cat} | 共{len(items)}条=====",
        })
        
        for item in items:
            row = dict(item)
            row['id'] = id_counter
            row['test_allow'] = True
            final_output.append(row)
            id_counter += 1
    
    total = id_counter - 1
    print(f"\n最终输出: {total} 条")
    
    print("\n分类统计:")
    for cat in CATEGORY_ORDER:
        n = len(category_items.get(cat, []))
        if n:
            print(f"  {cat}: {n} 条")
    
    return final_output, total


def write_csv(final_data, output_path):
    headers = [
        'id', 'food_name', 'alias', 'food_category',
        'calorie(kcal/100g)', 'protein(g/100g)', 'fat(g/100g)', 'carb(g/100g)',
        'diet_fiber(g/100g)', 'calcium(mg/100g)', 'gi_value',
        'folic_acid(μg)', 'dha(mg)', 'show_gi', 'show_folic_acid', 'show_dha',
        'test_allow', 'remark'
    ]
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(','.join(headers) + '\n')
        
        for row in final_data:
            if row.get('__header__'):
                f.write(row['text'] + '\n')
                continue
            
            csv_row = []
            for h in headers:
                val = row.get(h, '')
                if val is None:
                    csv_row.append('')
                elif isinstance(val, bool):
                    csv_row.append('True' if val else 'False')
                elif isinstance(val, float):
                    csv_row.append(f"{round1(val)}")
                else:
                    csv_row.append(str(val))
            f.write(','.join(csv_row) + '\n')
    
    print(f"\n已写入: {output_path}")


def main():
    final_data, count = process()
    write_csv(final_data, OUTPUT_CSV)
    print(f"\n{'='*60}")
    print(f"完成！共生成 {count} 条食材数据")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
