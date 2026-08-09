"""深入查看列表页真实 HTML 结构"""
import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://nlc.chinanutri.cn/fq/",
}

url = "https://nlc.chinanutri.cn/fq/foodlist_0_12_0_0_0_1.htm"
resp = requests.get(url, headers=headers, timeout=15)
resp.encoding = resp.apparent_encoding or "utf-8"
print(f"Status: {resp.status_code}, Length: {len(resp.text)}, Encoding: {resp.encoding}")

soup = BeautifulSoup(resp.text, "html.parser")

# 查找 iframe
iframes = soup.find_all("iframe")
print(f"\niframe 数量: {len(iframes)}")
for i, ifr in enumerate(iframes):
    print(f"  iframe {i}: src={ifr.get('src')}, id={ifr.get('id')}, name={ifr.get('name')}")

# 查找所有 a 标签（含 foodinfo 的）
all_links = soup.find_all("a", href=True)
print(f"\n总链接数: {len(all_links)}")
print("\n前 30 个链接（含 href）:")
for a in all_links[:30]:
    href = a["href"]
    text = a.get_text(strip=True)[:30]
    print(f"  [{text}] -> {href}")

# 查找可能的食物列表容器
print("\n--- 查找含食物名的元素 ---")
# 食物名通常在 td 或 li 或 div 中
for tag_name in ["td", "li", "div", "span"]:
    elements = soup.find_all(tag_name)
    food_candidates = []
    for el in elements:
        text = el.get_text(strip=True)
        # 食物名通常 2-15 字，含中文
        if 2 <= len(text) <= 20 and any('\u4e00' <= c <= '\u9fff' for c in text):
            # 排除明显的导航/分类文本
            if text not in ["蔬菜类及制品", "根菜类", "鲜豆类", "茄果、瓜菜类",
                            "葱蒜类", "嫩茎、叶、花菜类", "水生蔬菜类",
                            "薯芋类", "野生蔬菜类", "全部", "首页",
                            "食物营养成分查询平台", "搜 索", "搜索",
                            "中国疾病预防控制中心营养与健康所"]:
                a_in = el.find("a", href=True)
                if a_in:
                    food_candidates.append((text, a_in["href"], tag_name))
    if food_candidates:
        print(f"\n{tag_name} 中找到 {len(food_candidates)} 个候选食物:")
        for text, href, tag in food_candidates[:10]:
            print(f"  <{tag}> [{text}] -> {href}")
        break

# 查找 form（可能是 POST 搜索）
forms = soup.find_all("form")
print(f"\nform 数量: {len(forms)}")
for i, f in enumerate(forms):
    print(f"  form {i}: action={f.get('action')}, method={f.get('method')}")

# 查找 script 中的 AJAX/数据 URL
import re
scripts = soup.find_all("script")
print(f"\nscript 数量: {len(scripts)}")
for i, s in enumerate(scripts):
    if s.string:
        # 查找可能的 AJAX URL 或数据加载逻辑
        if any(kw in s.string for kw in ["foodinfo", "ajax", "load", "query", "list"]):
            print(f"\n=== script {i} (含关键词) ===")
            # 提取关键片段
            content = s.string
            for kw in ["foodinfo", "ajax", "load", "query", "list", "url"]:
                for m in re.finditer(rf'.{{0,80}}{kw}.{{0,80}}', content, re.IGNORECASE):
                    print(f"  ...{m.group(0)[:160]}...")
                    break

# 输出原始 HTML 片段（前 3000 字符）
print("\n\n=== HTML 前 3000 字符 ===")
print(resp.text[:3000])

# 输出 HTML 中间部分（找食物列表区域）
print("\n\n=== HTML 5000-9000 字符 ===")
print(resp.text[5000:9000])
