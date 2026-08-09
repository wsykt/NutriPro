"""探查 chinanutri 真实 HTML 结构"""
import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# 1. 详情页结构
print("=" * 70)
print("1. 详情页 https://nlc.chinanutri.cn/fq/foodinfo/371.html")
print("=" * 70)
resp = requests.get("https://nlc.chinanutri.cn/fq/foodinfo/371.html",
                    headers=headers, timeout=15)
resp.encoding = resp.apparent_encoding or "utf-8"
print(f"Status: {resp.status_code}, Encoding: {resp.encoding}, Length: {len(resp.text)}")

soup = BeautifulSoup(resp.text, "html.parser")

# 标题
h1 = soup.find("h1")
print(f"\nH1: {h1.get_text(strip=True) if h1 else 'None'}")
if h1:
    print(f"H1 HTML: {str(h1)[:300]}")

# 食物类、亚类（在 h1 附近）
if h1:
    print("\n--- h1 后续文本节点（找食物类/亚类）---")
    for sib in h1.find_all_next(string=True)[:30]:
        s = str(sib).strip()
        if s and ("类" in s or "亚类" in s or "食部" in s):
            print(f"  text: {s[:80]}")

# 表格
tables = soup.find_all("table")
print(f"\n表格数量: {len(tables)}")
for i, t in enumerate(tables):
    print(f"\n=== Table {i} ===")
    print(f"  class: {t.get('class')}")
    rows = t.find_all("tr")
    print(f"  行数: {len(rows)}")
    # 打印前 3 行的 HTML 结构
    for r in rows[:3]:
        cells = r.find_all(["td", "th"])
        print(f"  行[{len(cells)}格]: ", end="")
        for c in cells:
            txt = c.get_text(strip=True)
            print(f"[{txt[:30]}]", end=" ")
        print()
    # 打印 class 属性样本
    if rows:
        first_row = rows[0]
        for c in first_row.find_all(["td", "th"]):
            cls = c.get("class")
            if cls:
                print(f"  cell class: {cls}, text: {c.get_text(strip=True)[:30]}")

# 2. 列表页结构
print("\n\n" + "=" * 70)
print("2. 列表页 https://nlc.chinanutri.cn/fq/foodlist_0_12_0_0_0_1.htm")
print("=" * 70)
resp2 = requests.get("https://nlc.chinanutri.cn/fq/foodlist_0_12_0_0_0_1.htm",
                     headers=headers, timeout=15)
resp2.encoding = resp2.apparent_encoding or "utf-8"
print(f"Status: {resp2.status_code}, Length: {len(resp2.text)}")

soup2 = BeautifulSoup(resp2.text, "html.parser")
# 找所有 foodinfo 链接
links = []
for a in soup2.find_all("a", href=True):
    href = a["href"]
    text = a.get_text(strip=True)
    if "foodinfo" in href or "foodlist" in href:
        links.append((text, href))

print(f"\n食物链接数: {len([l for l in links if 'foodinfo' in l[1]])}")
print("前 10 个食物链接:")
for text, href in links[:10]:
    if "foodinfo" in href:
        print(f"  {text} -> {href}")

# 分页结构
print("\n分页链接:")
for text, href in links:
    if "foodlist" in href and href != "/fq/foodlist_0_12_0_0_0_1.htm":
        print(f"  {text} -> {href}")

# 3. 搜索结果页
print("\n\n" + "=" * 70)
print("3. 搜索页 鸡蛋")
print("=" * 70)
search_url = "https://nlc.chinanutri.cn/fq/foodlist_%E9%B8%A1%E8%9B%8B_0_0_0_0_1.htm"
resp3 = requests.get(search_url, headers=headers, timeout=15)
resp3.encoding = resp3.apparent_encoding or "utf-8"
print(f"Status: {resp3.status_code}, Length: {len(resp3.text)}")

soup3 = BeautifulSoup(resp3.text, "html.parser")
search_links = []
for a in soup3.find_all("a", href=True):
    href = a["href"]
    text = a.get_text(strip=True)
    if "foodinfo" in href:
        search_links.append((text, href))

print(f"\n搜索结果中食物链接数: {len(search_links)}")
for text, href in search_links[:10]:
    print(f"  {text} -> {href}")

# 4. 首页分类入口
print("\n\n" + "=" * 70)
print("4. 首页分类 https://nlc.chinanutri.cn/fq/")
print("=" * 70)
resp4 = requests.get("https://nlc.chinanutri.cn/fq/", headers=headers, timeout=15)
resp4.encoding = resp4.apparent_encoding or "utf-8"
soup4 = BeautifulSoup(resp4.text, "html.parser")
print(f"Status: {resp4.status_code}, Length: {len(resp4.text)}")

print("\n首页所有 foodlist 链接:")
seen = set()
for a in soup4.find_all("a", href=True):
    href = a["href"]
    text = a.get_text(strip=True)
    if "foodlist" in href and href not in seen:
        seen.add(href)
        print(f"  {text} -> {href}")
