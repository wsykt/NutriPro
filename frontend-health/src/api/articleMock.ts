import { api } from '@/api'

/** 文章篇幅类型：short=速读卡, medium=深度文, long=综述文 */
export type LengthType = 'short' | 'medium' | 'long'

export interface Article {
  id: number
  title: string
  topic: string
  topicGroupId: string
  lengthType: LengthType
  icon?: string
  content: string
  contentShort?: string
  contentMedium?: string
  contentLong?: string
  summary: string
  summaryShort?: string
  summaryMedium?: string
  summaryLong?: string
  tags?: string
  category: string
  audience: string
  wordCount?: number
  sourcesJson?: string
  viewsCount?: number
  likesCount?: number
  createdAt?: string
  updatedAt?: string
  status?: string
  source?: string
  qualityScore?: number
  hasErrorsReported?: boolean
  authorName?: string
}

/** 篇幅中文标签 */
export const LEN_LABEL: Record<LengthType, string> = {
  short: '速读卡',
  medium: '深度文',
  long: '综述文'
}

/** 篇幅徽章配色（贴合 morandi 主题：深度文用主题绿，其余用互补色） */
export const LEN_COLOR: Record<LengthType, string> = {
  short: 'bg-sky-50 text-sky-700 border-sky-200',
  medium: 'bg-morandi-accent/10 text-morandi-accent border-morandi-accent/30',
  long: 'bg-violet-50 text-violet-700 border-violet-200'
}

/** 篇幅 Tab 配置 */
export const LEN_TABS = [
  { key: 'short' as LengthType, label: '速读卡', desc: '1分钟速览核心要点', approx: '≈300字', hint: '没时间就看它' },
  { key: 'medium' as LengthType, label: '深度文', desc: '循证论证 + 实操方案', approx: '≈1500字', hint: '推荐首选' },
  { key: 'long' as LengthType, label: '综述文', desc: '含学术争议 + 前沿', approx: '≈2500字', hint: '深度学习' }
]

// ============ Mock 科普文章数据（4 主题 × 3 篇幅 = 12 条） ============
const S: LengthType = 'short', M: LengthType = 'medium', L: LengthType = 'long'

const intro_cal = '随着我国老龄化进程加速，60 岁以上人群骨质疏松患病率已超过 36%（中国居民营养与慢性病状况报告），钙摄入不足是直接诱因之一。'
const common_cal = `## 一、每天需要多少钙？
不同人群每日推荐钙摄入量（中国居民膳食指南 2022）：
- **18-49 岁成年人**：800 mg
- **50 岁以上 / 孕中晚期 / 乳母**：1000 mg
- **可耐受最高摄入量**：2000 mg/天

## 二、高钙食物 TOP 清单
| 食物（每100g可食部） | 钙含量（mg） | 备注 |
|---|---|---|
| 奶酪（切达） | 730 | 吸收率高，注意脂肪 |
| 豆腐干（北） | 308 | 性价比最高 |
| 牛乳 | 104 | 液体钙，睡前喝更佳 |
| 酸奶 | 118 | 乳糖不耐受首选 |
| 黑芝麻 | 780 | 注意每日用量≤20g |
| 虾皮 | 991 | 钠高，煮汤用 |

## 三、促进吸收的关键：维生素 D + 运动
- **维生素 D**：晒太阳 15-20 分钟/天，或补充 VD3 400-800 IU/天
- **负重运动**：快走、爬楼、太极拳，每周 3 次×30 分钟
- **减少流失**：少喝浓茶、浓咖啡、高盐食物，戒烟限酒`
const deep_cal = `## 四、补钙的 3 个常见误区
### 误区 1：骨头汤能补钙
一碗猪骨汤仅含钙 ≈ 5 mg，且嘌呤和脂肪高，不如一杯牛奶（250 ml≈260 mg）实在。

### 误区 2：钙片随便吃
一次性补充超过 500 mg 吸收率会显著下降，建议**分 2 次**随餐服用。肾结石病史者需先评估尿钙水平。

### 误区 3：只补钙不补镁和 K2
镁参与骨基质形成，维生素 K2 引导钙沉积到骨骼而非血管。建议搭配深绿色叶菜（镁）+ 纳豆（K2）。

## 五、特殊人群方案
- **绝经后女性**：建议骨密度检测，T-score≤-2.5 需药物干预+1200 mg 钙+800 IU VD
- **儿童青少年**：优先食物补充，牛奶 300-500 ml/天，钙片仅在饮食不足时使用
- **慢性肾病患者**：避免过量补钙，需监测血钙和甲状旁腺激素，遵从肾内科医嘱`
const debate_cal = `## 六、学术争议与前沿
### 争议 1：高钙摄入是否增加心血管风险？
近年 JAMA、BMJ 多项观察性研究提示**男性总钙摄入＞1500 mg/天**可能与心血管事件风险轻度升高相关，但 RCT 证据不支持该结论。目前学界共识：在推荐范围内（≤2000 mg/天）是安全的，**优先食物来源**。

### 争议 2：有机钙 vs 无机钙，谁更好？
柠檬酸钙、乳酸钙等有机钙溶解度高、对胃刺激小，适合胃酸不足人群，但**单位体积含钙量低、价格高**；碳酸钙性价比最高，随餐服用即可。不存在绝对的"有机就更好"，需结合个体胃内环境和经济状况选择。

### 研究前沿
2025 年发表在 *Journal of Bone and Mineral Research* 的 Meta 分析提示：**钙 + 维生素 D 联合补充 + 适量蛋白质摄入**，对老年人髋部骨折预防的复合终点风险降低 18%，是未来指南修订的重要参考。`

const intro_salt = '《中国居民营养与慢性病状况报告 2022》显示，我国 18 岁及以上居民高血压患病率为 27.5%，人均每日食盐摄入量达 9.3 g，远超 WHO 推荐的 5 g。'
const common_salt = `## 一、控盐的核心数字
- **健康成人**：≤5 g/天（约 1 啤酒瓶盖，含隐形盐）
- **高血压/肾病患者**：≤3 g/天
- **1 岁内婴儿**：0 g（严禁额外加盐）
- **1 g 盐 ≈ 400 mg 钠**

## 二、隐形盐的 6 大藏身地
很多食物吃起来不咸，但钠含量惊人：
1. **调味品**：酱油 10 ml≈1.6 g 盐，蚝油、豆瓣酱同理
2. **加工肉类**：100 g 火腿≈1.5-2 g 盐
3. **零食**：一包 100 g 薯片≈1.2 g 盐
4. **腌制菜**：100 g 咸菜≈5-15 g 盐
5. **方便食品**：一碗方便面≈5-8 g 盐
6. **面点**：100 g 挂面/面包≈0.5-1 g 盐

## 三、减盐实操技巧
- **烹饪后放盐**：盐撒在食物表面，味蕾感知更强
- **使用限盐勺**：2 g 勺是家庭标配
- **替代调味**：用葱姜蒜、柠檬、香草、胡椒粉、花椒提味
- **看营养标签**：选择钠 NRV%≤30% 的食品，警惕"低钠"≠无钠
- **多吃钾**：香蕉、土豆、菠菜、牛油果帮助排钠`
const deep_salt = `## 四、DASH 饮食模式：高血压的"饮食处方"
DASH（Dietary Approaches to Stop Hypertension）饮食是目前唯一被美国 NIH 写入高血压防治指南的饮食模式，坚持 8 周可使收缩压下降 8-14 mmHg。

**核心原则（每日）：**
| 食物组 | 份数 | 示例 |
|---|---|---|
| 全谷杂粮 | 7-8 份 | 糙米、燕麦、全麦面包 |
| 蔬菜水果 | 8-10 份 | 深色蔬菜 + 彩虹水果 |
| 低脂乳制品 | 2-3 份 | 低脂奶、无糖酸奶 |
| 瘦肉禽鱼 | ≤2 份 | 去皮鸡胸肉、深海鱼 |
| 坚果豆类 | 4-5 份/周 | 杏仁、鹰嘴豆 |
| 油脂甜食 | 少量 | 橄榄油，避免反式脂肪 |

## 五、低钠盐适用人群与禁忌
- **适用**：一般健康人群、原发性高血压患者
- **禁忌**：慢性肾病 3b 期以上、高钾血症、使用保钾利尿剂者，因低钠盐中约 25% 的钠被钾替代，有高钾血症风险。建议咨询医生或营养师。`
const debate_salt = `## 六、学术争议与前沿
### 争议 1：J 型曲线是否真的存在？
观察性研究发现：极端低钠（＜3 g/天）人群心血管事件反而升高，形成"J 型曲线"。但最新 2024 年 Cochrane 系统综述指出，**该现象仅出现在有基础疾病的群体**，在健康人群中，从 12 g 逐步减到 5 g 的线性获益是明确的。对普通大众，**没必要在 5 g 以下再极端减盐**。

### 争议 2：钾盐替代的人群差异
东亚人群（中日韩）盐敏感性普遍高于欧美，低钠盐在该人群中效果更显著，但**慢性肾病流行率也更高**。2025 年 *Lancet Global Health* 的 SSaSS 研究 5 年随访证实：在 60 岁以上、有脑卒中史的人群中，使用钾盐替代组卒中年风险降低 11%，但需在干预前进行肾功能筛查。

### 研究前沿
肠道微生物群对钠代谢的影响成为新靶点：部分 Akkermansia 菌株可通过调节肠上皮钠通道表达影响钠吸收。未来 3-5 年可能出现"益生菌 + 限盐"的复合干预方案。`

const intro_gym = `《全民健身计划》数据显示，我国经常参加体育锻炼人数比例已达 38.5%，但运动后蛋白质补充不足、过量或时机错误的情况十分普遍，直接影响增肌效果和恢复。`
const common_gym = `## 一、蛋白质需要量
不同训练目标的每日蛋白质摄入（按瘦体重 LBM 计算，若不知瘦体重可用总体重 × 0.75 估算）：
| 目标 | 每日摄入量（g/kg 体重） | 蛋白质供能比 |
|---|---|---|
| 普通健康人 | 0.8-1.0 | 10-15% |
| 减脂期（有氧为主） | 1.2-1.6 | 25-30% |
| 增肌期（力量训练） | 1.6-2.2 | 20-25% |
| 极限备赛期 | 2.2-2.6 | ≤35% |
| 中老年运动者 | 1.2-1.6 | 预防肌少症 |

## 二、蛋白质来源评分
**PDCAAS（蛋白质消化率校正氨基酸评分）满分 1.0：**
| 食物 | 评分 | 氨基酸限制 |
|---|---|---|
| 乳清蛋白 | 1.0 | 无 |
| 鸡蛋全蛋 | 1.0 | 无 |
| 大豆分离蛋白 | 1.0 | 无 |
| 牛肉 | 0.92 | 色氨酸略低 |
| 花生 | 0.52 | 赖氨酸、苏氨酸 |
| 小麦 | 0.42 | 赖氨酸严重不足 |

**建议**：植物蛋白互补原则——谷物 + 豆类（如米饭+豆腐、全麦面包+花生酱）可使氨基酸谱接近完全蛋白。

## 三、补充时机与分配
- **训练窗口**：训练前后 2 小时内补充 20-40 g 完全蛋白，窗口之外影响不大
- **均匀分配**：将每日蛋白总量平均分配到 3-4 餐，每餐 25-40 g，单次超过 40 g 无额外合成代谢增益
- **睡前补充**：30-40 g 酪蛋白可延长夜间肌肉蛋白合成，改善次日恢复`
const deep_gym = `## 四、乳清 vs 酪蛋白 vs 植物蛋白，怎么选？
| 类型 | 吸收速度 | 适用场景 | 注意 |
|---|---|---|---|
| 乳清（Whey） | 快（1-2 h 峰） | 训练后即刻 | 乳糖不耐受选分离型 WPI |
| 酪蛋白（Casein） | 慢（6-8 h） | 睡前 / 长时间空腹 | 肾结石病史者注意监测 |
| 大豆分离蛋白（SPI） | 中 | 素食 / 降血脂 | 搭配 B12、铁补充 |
| 豌豆蛋白 | 中慢 | 过敏友好 | 支链氨基酸含量低于乳清 |

**蛋白粉不是必需**：饮食能达到总目标量时，无需额外补充补剂。优先食物来源。

## 五、减脂期的蛋白质策略
减脂期若要最大化保留瘦体重，建议：
1. 每日总热量缺口控制在 300-500 kcal，不要极端节食
2. 蛋白质提高到 1.6-2.2 g/kg，并搭配每周 2-3 次抗阻训练
3. 每 2 周监测一次腰围、体重和力量，避免掉肌肉的过快减重（＞1% 体重/周）
4. 碳水化合物保持中等摄入（≥3-4 g/kg），否则蛋白质会被糖异生消耗掉`
const debate_gym = `## 六、学术争议与前沿
### 争议 1：2.2 g/kg 以上是否真的有效？
ISSN 和 ACSM 长期推荐 1.6-2.2 g/kg 为增肌上限，但 2024 年 *Journal of the International Society of Sports Nutrition* 发表的多中心 RCT 显示：**经验丰富（训练年限 ≥4 年）的自然健美训练者**，在 2.4 vs 3.2 g/kg 的对比中，3.2 g 组在 lean mass 变化上无统计学显著差异，但主观饱腹感提升更明显。结论：**2.2 g/kg 已是实际平台值**，更高摄入更多是个人偏好而非必需。

### 争议 2：训练前 vs 训练后蛋白补充
传统观点推崇"合成代谢窗口"为训练后 1-2 小时，但近年 20+ 研究的 Meta 分析（2023）提示：**只要全天总量达标且分布合理，训练前后 6 小时内的补充时机差异在统计学上不显著**。对普通爱好者，规律训练+均衡饮食比纠结补剂时间更重要。

### 研究前沿
亮氨酸阈值（≥2.5-3 g/餐触发最大 MPS）正在被重新审视：2025 年 *American Journal of Clinical Nutrition* 研究表明，老年人群的亮氨酸"应答阈值"比年轻人高约 50%，推荐每餐亮氨酸 ≥3.5-4 g（如 50 g 牛肉 + 2 个鸡蛋），对应蛋白质约 40-50 g/餐。这将改写未来老年运动营养指南。`

const intro_gut = `现代社会约 40% 的成年人存在不同程度的胃肠道不适（《Nature Gastroenterology & Hepatology》2024），饮食结构失衡是肠道菌群紊乱的主要诱因。`
const common_gut = `## 一、好肠道的 4 个饮食原则
### 1. 足够的膳食纤维
- **目标**：成年人 25-30 g/天
- **来源**：全谷物（燕麦、糙米）、杂豆、深绿色叶菜、菌菇类
- **循序渐进**：突然大量增加会产气腹胀，每周增加 5 g

### 2. 益生菌 + 益生元双管齐下
- **益生菌（活菌）**：无糖酸奶、纳豆、韩国泡菜、开菲尔
- **益生元（菌的粮食）**：洋葱、大蒜、芦笋、香蕉（稍生更好）、菊苣根

### 3. 充足水分 + 规律运动
- 每天 1500-2000 ml 白开水，膳食纤维需水才能膨胀
- 每天 30 分钟中等强度有氧运动，刺激肠道蠕动

### 4. 限制 5 类伤肠食物
- 大量精加工食品（反式脂肪 + 添加剂）
- 高糖饮料（游离糖＞25 g/天有害菌增殖）
- 过度饮酒
- 频繁使用抗生素（需补充益生菌）
- 辛辣刺激（因人而异，适度即可）`
const deep_gut = `## 二、FODMAP 饮食：肠易激综合征（IBS）的阶梯方案
对于 IBS 患者（腹胀、腹痛、排便习惯改变），低 FODMAP 饮食 4-6 周，可使 50-70% 患者症状缓解。**FODMAP** 指易发酵的短链碳水：
- **F**ermentable 发酵性
- **O**ligosaccharides 寡糖（小麦、豆类、洋葱）
- **D**isaccharides 双糖（乳糖）
- **M**onosaccharides 单糖（果糖）
- **A**nd **P**olyols 多元醇（甜味剂、核果类水果）

**严格实施必须在营养师指导下进行**，因为寡糖恰恰是双歧杆菌的优质食物，长期严格低 FODMAP 反而会破坏菌群多样性。标准流程是：
1. 排除期（4-6 周）→ 2. 再引入期（逐个验证）→ 3. 个性化维持期

## 三、肠-脑轴：情绪和肠道的双向调节
血清素（5-HT）约 90% 在肠道合成。2024 年 *Cell Reports Medicine* 研究显示：**抑郁症患者 Akkermansia muciniphila 丰度显著降低**，补充 8 周 Akk + 有氧运动，HAMD 评分改善 22%。

**日常情绪友好食物**：发酵乳制品、深海水产（Omega-3 + 维生素 D）、黑巧克力（70%+ 可可）、富含色氨酸的坚果（南瓜籽、杏仁）。
建议咨询医生或营养师后制定个性化方案。`
const debate_gut = `## 四、学术争议与前沿
### 争议 1：益生菌补充剂到底有没有用？
*New England Journal of Medicine* 2023 年刊发多篇 RCT：**健康人群日常补充商业益生菌，多数终点指标（菌群多样性、免疫指标）变化不显著**，且停用后效果 3 个月内消退。但在**抗生素后腹泻、IBS、艰难梭菌复发预防**等特定适应症中，益生菌有明确证据支持。结论：普通人喝无糖酸奶即可，特殊人群在医生指导下使用特定菌株（如 LGG、布拉酵母菌）。

### 争议 2：纤维超量是否有害？
部分肠道敏感人群，每日纤维＞45 g 时出现腹胀、便秘加重，并可能影响铁、钙、锌吸收。但目前在大规模流行病学研究中，**高纤维摄入（≤50 g/天）的长期获益远大于风险**。真正的问题是"纤维类型是否合适"（如 IBS 患者应选择可溶性>不溶性）。

### 研究前沿
2025 年 *Nature Medicine* 发表的"微生物组精准营养"前瞻性研究表明：结合个体肠道菌群基线 + 餐后血糖反应 + 生活方式因素，可以为每人预测个性化的"血糖友好食物清单"，相比通用健康饮食建议，餐后 2h 血糖 AUC 额外降低 17%。AI + 微生物组正在开启**营养 5.0 个性化时代**。`

/** 按 h2 标题分割（不误拆 h3），用于生成速读卡 */
function splitIntoH2Sections(text: string): string[] {
  const positions: number[] = []
  const h2Regex = /^## (?!#)/gm
  let match: RegExpExecArray | null
  while ((match = h2Regex.exec(text)) !== null) {
    positions.push(match.index)
  }
  if (positions.length === 0) return [text]
  const result: string[] = []
  for (let i = 0; i < positions.length; i++) {
    const start = positions[i]
    const end = i + 1 < positions.length ? positions[i + 1] : text.length
    result.push(text.substring(start, end).trim())
  }
  return result
}

function genArticle(
  id: number, topicGroup: string, title: string, category: string, audience: string,
  lengthType: LengthType, intro: string, common: string, deep: string, debate: string,
  summaryS: string, summaryM: string, summaryL: string, date: string, icon: string,
  _extra?: string
): Article {
  const shortC = intro + '\n\n' + splitIntoH2Sections(common).slice(0, 3).join('\n\n').trim() + '\n\n**速读结论：**' + summaryS
  const mediumC = intro + '\n\n' + common + '\n\n' + deep
  const longC = intro + '\n\n' + common + '\n\n' + deep + '\n\n' + debate

  const isShort = lengthType === S
  const isMedium = lengthType === M
  const titleSuffix = isShort ? '【速读卡】' : lengthType === L ? '【综述文】' : '【深度文】'
  const summary0 = isShort ? summaryS : lengthType === L ? summaryL : summaryM
  const wc = (isShort ? shortC : isMedium ? mediumC : longC).replace(/[^\u4e00-\u9fa5]/g, '').length

  const sources = [
    '[1] 中国营养学会. 中国居民膳食指南（2022）. 人民卫生出版社. 2022.',
    '[2] 中国居民营养与慢性病状况报告（2022 年）. 国家卫生健康委. 2022.',
    '[3] World Health Organization. Guideline: Sodium intake for adults and children. 2012.',
    '[4] U.S. Department of Health and Human Services & USDA. Dietary Guidelines for Americans 2025-2030.',
    '[5] 中华医学会肠外肠内营养学分会. 中国肿瘤患者围术期营养支持治疗指南. 2024.',
    '[6] ISSN Position Stand: Protein and Exercise. J Int Soc Sports Nutr. 2024.'
  ]

  return {
    id,
    title: title + titleSuffix,
    topic: topicGroup,
    topicGroupId: 'tg-' + topicGroup,
    lengthType,
    icon,
    content: isShort ? shortC : isMedium ? mediumC : longC,
    contentShort: shortC,
    contentMedium: mediumC,
    contentLong: longC,
    summary: summary0,
    summaryShort: summaryS,
    summaryMedium: summaryM,
    summaryLong: summaryL,
    tags: JSON.stringify([category, audience]),
    category,
    audience,
    wordCount: wc,
    sourcesJson: JSON.stringify(sources),
    viewsCount: Math.floor(Math.random() * 9000 + 1000),
    likesCount: Math.floor(Math.random() * 600 + 50),
    createdAt: date,
    updatedAt: date,
    status: 'published',
    source: 'ai',
    qualityScore: 80 + Math.floor(Math.random() * 20),
    hasErrorsReported: false,
    authorName: 'AI健康助手'
  }
}

export const MOCK_ARTICLES: Article[] = [
  // 主题 1：补钙
  genArticle(1, 'calcium', '老年人群如何科学补钙', '慢病管理', '老年人', S, intro_cal, common_cal, deep_cal, debate_cal,
    '补钙速览：每日800-1000 mg，牛奶/北豆腐/黑芝麻为主，搭配VD3 400 IU+每周负重运动3次。',
    '补钙速览：每日800-1000 mg，牛奶/北豆腐/黑芝麻为主，搭配VD3 400 IU+每周负重运动3次。',
    '补钙的完整方案：剂量、高钙食物清单、吸收要点（VD、K2、镁）+ 避坑指南（骨头汤无效、钙片分次服）+ 绝经后/肾病等特殊人群注意事项。',
    '补钙的循证综述：推荐值→高钙食物→吸收促进→常见误区→特殊人群方案→心血管风险争议、有机钙vs无机钙争议、最新联合补充Meta分析。',
    '2026-07-01', 'calcium'),
  genArticle(2, 'calcium', '老年人群如何科学补钙', '慢病管理', '老年人', M, intro_cal, common_cal, deep_cal, debate_cal,
    '补钙速览：每日800-1000 mg，牛奶/北豆腐/黑芝麻为主，搭配VD3 400 IU+每周负重运动3次。',
    '补钙速览：每日800-1000 mg，牛奶/北豆腐/黑芝麻为主，搭配VD3 400 IU+每周负重运动3次。',
    '补钙的完整方案：剂量、高钙食物清单、吸收要点（VD、K2、镁）+ 避坑指南（骨头汤无效、钙片分次服）+ 绝经后/肾病等特殊人群注意事项。',
    '补钙的循证综述：推荐值→高钙食物→吸收促进→常见误区→特殊人群方案→心血管风险争议、有机钙vs无机钙争议、最新联合补充Meta分析。',
    '2026-07-01', 'calcium'),
  genArticle(3, 'calcium', '老年人群如何科学补钙', '慢病管理', '老年人', L, intro_cal, common_cal, deep_cal, debate_cal,
    '补钙速览：每日800-1000 mg，牛奶/北豆腐/黑芝麻为主，搭配VD3 400 IU+每周负重运动3次。',
    '补钙速览：每日800-1000 mg，牛奶/北豆腐/黑芝麻为主，搭配VD3 400 IU+每周负重运动3次。',
    '补钙的完整方案：剂量、高钙食物清单、吸收要点（VD、K2、镁）+ 避坑指南（骨头汤无效、钙片分次服）+ 绝经后/肾病等特殊人群注意事项。',
    '补钙的循证综述：推荐值→高钙食物→吸收促进→常见误区→特殊人群方案→心血管风险争议、有机钙vs无机钙争议、最新联合补充Meta分析。',
    '2026-07-01', 'calcium'),

  // 主题 2：减盐
  genArticle(4, 'salt', '高血压人群如何控盐降压', '慢病管理', '高血压', S, intro_salt, common_salt, deep_salt, debate_salt,
    '控盐速览：每日≤5 g，警惕6类隐形盐；烹饪后放盐+用葱姜蒜提味。',
    '控盐速览：健康人≤5 g/天，高血压≤3 g；警惕6类隐形盐；烹饪后放盐、用葱姜蒜柠檬替代、DASH饮食模式效果明确。',
    '控盐+DASH饮食的完整方案：每日推荐量、隐形盐识别清单、减盐实操4技巧，以及DASH饮食的每日食物分配表、低钠盐的适用与禁忌。',
    '控盐的循证综述：流行病学数据→6类隐形盐→减盐实操→DASH循证饮食→低钠盐风险→J型曲线争议、东亚人群钾盐替代SSaSS 5年随访结果、肠道菌群新靶点。',
    '2026-07-05', 'salt'),
  genArticle(5, 'salt', '高血压人群如何控盐降压', '慢病管理', '高血压', M, intro_salt, common_salt, deep_salt, debate_salt,
    '控盐速览：每日≤5 g，警惕6类隐形盐；烹饪后放盐+用葱姜蒜提味。',
    '控盐速览：健康人≤5 g/天，高血压≤3 g；警惕6类隐形盐；烹饪后放盐、用葱姜蒜柠檬替代、DASH饮食模式效果明确。',
    '控盐+DASH饮食的完整方案：每日推荐量、隐形盐识别清单、减盐实操4技巧，以及DASH饮食的每日食物分配表、低钠盐的适用与禁忌。',
    '控盐的循证综述：流行病学数据→6类隐形盐→减盐实操→DASH循证饮食→低钠盐风险→J型曲线争议、东亚人群钾盐替代SSaSS 5年随访结果、肠道菌群新靶点。',
    '2026-07-05', 'salt'),
  genArticle(6, 'salt', '高血压人群如何控盐降压', '慢病管理', '高血压', L, intro_salt, common_salt, deep_salt, debate_salt,
    '控盐速览：每日≤5 g，警惕6类隐形盐；烹饪后放盐+用葱姜蒜提味。',
    '控盐速览：健康人≤5 g/天，高血压≤3 g；警惕6类隐形盐；烹饪后放盐、用葱姜蒜柠檬替代、DASH饮食模式效果明确。',
    '控盐+DASH饮食的完整方案：每日推荐量、隐形盐识别清单、减盐实操4技巧，以及DASH饮食的每日食物分配表、低钠盐的适用与禁忌。',
    '控盐的循证综述：流行病学数据→6类隐形盐→减盐实操→DASH循证饮食→低钠盐风险→J型曲线争议、东亚人群钾盐替代SSaSS 5年随访结果、肠道菌群新靶点。',
    '2026-07-05', 'salt'),

  // 主题 3：健身蛋白质
  genArticle(7, 'protein', '健身人群蛋白质摄入全指南', '运动营养', '健身人群', S, intro_gym, common_gym, deep_gym, debate_gym,
    '蛋白速览：增肌1.6-2.2 g/kg/天，乳清/鸡蛋/大豆满分来源，每餐25-40 g均匀分配。',
    '蛋白速览：增肌1.6-2.2 g/kg/天，减脂期1.6-2.2 g保肌；乳清/鸡蛋/大豆PDCAAS满分；每日3-4餐均匀分配25-40 g；睡前30-40 g酪蛋白。',
    '健身蛋白质完整方案：目标摄入量表、PDCAAS来源评分、补充时机分配；乳清/酪蛋白/大豆/豌豆蛋白详细对比；减脂期 300-500 kcal缺口 + 2-3次抗阻 + 充足碳水。',
    '健身蛋白质循证综述：摄入量→来源评分→分配策略→补剂选择→减脂期策略→2.2 g以上真的有用吗？训练前后窗口到底重不重要？老年人亮氨酸阈值修正（3.5-4 g/餐）。',
    '2026-07-10', 'protein'),
  genArticle(8, 'protein', '健身人群蛋白质摄入全指南', '运动营养', '健身人群', M, intro_gym, common_gym, deep_gym, debate_gym,
    '蛋白速览：增肌1.6-2.2 g/kg/天，乳清/鸡蛋/大豆满分来源，每餐25-40 g均匀分配。',
    '蛋白速览：增肌1.6-2.2 g/kg/天，减脂期1.6-2.2 g保肌；乳清/鸡蛋/大豆PDCAAS满分；每日3-4餐均匀分配25-40 g；睡前30-40 g酪蛋白。',
    '健身蛋白质完整方案：目标摄入量表、PDCAAS来源评分、补充时机分配；乳清/酪蛋白/大豆/豌豆蛋白详细对比；减脂期 300-500 kcal缺口 + 2-3次抗阻 + 充足碳水。',
    '健身蛋白质循证综述：摄入量→来源评分→分配策略→补剂选择→减脂期策略→2.2 g以上真的有用吗？训练前后窗口到底重不重要？老年人亮氨酸阈值修正（3.5-4 g/餐）。',
    '2026-07-10', 'protein'),
  genArticle(9, 'protein', '健身人群蛋白质摄入全指南', '运动营养', '健身人群', L, intro_gym, common_gym, deep_gym, debate_gym,
    '蛋白速览：增肌1.6-2.2 g/kg/天，乳清/鸡蛋/大豆满分来源，每餐25-40 g均匀分配。',
    '蛋白速览：增肌1.6-2.2 g/kg/天，减脂期1.6-2.2 g保肌；乳清/鸡蛋/大豆PDCAAS满分；每日3-4餐均匀分配25-40 g；睡前30-40 g酪蛋白。',
    '健身蛋白质完整方案：目标摄入量表、PDCAAS来源评分、补充时机分配；乳清/酪蛋白/大豆/豌豆蛋白详细对比；减脂期 300-500 kcal缺口 + 2-3次抗阻 + 充足碳水。',
    '健身蛋白质循证综述：摄入量→来源评分→分配策略→补剂选择→减脂期策略→2.2 g以上真的有用吗？训练前后窗口到底重不重要？老年人亮氨酸阈值修正（3.5-4 g/餐）。',
    '2026-07-10', 'protein'),

  // 主题 4：肠道健康
  genArticle(10, 'gut', '肠道健康与饮食调理完全指南', '消化健康', '普通人群', S, intro_gut, common_gut, deep_gut, debate_gut,
    '肠道速览：每天25-30 g膳食纤维，无糖酸奶+纳豆补益生菌，洋葱大蒜补益生元。',
    '肠道速览：每日25-30 g膳食纤维（燕麦/糙米/杂豆/菌菇）；益生菌+益生元（无糖酸奶+洋葱大蒜）；充足水+规律运动；限精加工、糖、酒、滥用抗生素。',
    '肠道健康完整方案：4大饮食原则（纤维足量、菌+元双补、水分+运动、限制伤肠食物）；IBS患者FODMAP三阶段实施；肠-脑轴情绪友好食物（Akk菌+Omega3+70%黑巧）。',
    '肠道健康循证综述：4大原则→FODMAP阶梯方案→肠-脑轴2024 Akk菌抑郁研究→健康人补充商业益生菌真的有效吗？纤维超量的争议；2025 Nature Medicine 微生物组精准营养开启AI个性化时代。',
    '2026-07-15', 'gut'),
  genArticle(11, 'gut', '肠道健康与饮食调理完全指南', '消化健康', '普通人群', M, intro_gut, common_gut, deep_gut, debate_gut,
    '肠道速览：每天25-30 g膳食纤维，无糖酸奶+纳豆补益生菌，洋葱大蒜补益生元。',
    '肠道速览：每日25-30 g膳食纤维（燕麦/糙米/杂豆/菌菇）；益生菌+益生元（无糖酸奶+洋葱大蒜）；充足水+规律运动；限精加工、糖、酒、滥用抗生素。',
    '肠道健康完整方案：4大饮食原则（纤维足量、菌+元双补、水分+运动、限制伤肠食物）；IBS患者FODMAP三阶段实施；肠-脑轴情绪友好食物（Akk菌+Omega3+70%黑巧）。',
    '肠道健康循证综述：4大原则→FODMAP阶梯方案→肠-脑轴2024 Akk菌抑郁研究→健康人补充商业益生菌真的有效吗？纤维超量的争议；2025 Nature Medicine 微生物组精准营养开启AI个性化时代。',
    '2026-07-15', 'gut'),
  genArticle(12, 'gut', '肠道健康与饮食调理完全指南', '消化健康', '普通人群', L, intro_gut, common_gut, deep_gut, debate_gut,
    '肠道速览：每天25-30 g膳食纤维，无糖酸奶+纳豆补益生菌，洋葱大蒜补益生元。',
    '肠道速览：每日25-30 g膳食纤维（燕麦/糙米/杂豆/菌菇）；益生菌+益生元（无糖酸奶+洋葱大蒜）；充足水+规律运动；限精加工、糖、酒、滥用抗生素。',
    '肠道健康完整方案：4大饮食原则（纤维足量、菌+元双补、水分+运动、限制伤肠食物）；IBS患者FODMAP三阶段实施；肠-脑轴情绪友好食物（Akk菌+Omega3+70%黑巧）。',
    '肠道健康循证综述：4大原则→FODMAP阶梯方案→肠-脑轴2024 Akk菌抑郁研究→健康人补充商业益生菌真的有效吗？纤维超量的争议；2025 Nature Medicine 微生物组精准营养开启AI个性化时代。',
    '2026-07-15', 'gut')
]

/** 后端数据是否带新字段（lengthType）—— 缺字段时需回退 mock */
function hasNewFields(list: any[]): boolean {
  return Array.isArray(list) && list.length > 0 && !!(list[0] && list[0].lengthType)
}

/**
 * 拉取文章列表：优先后端，后端无数据或缺新字段时回退 mock。
 * 支持按 category / audience / lengthType 过滤。
 */
export async function fetchArticles(params?: {
  category?: string
  audience?: string
  lengthType?: LengthType | 'all'
  keyword?: string
}): Promise<Article[]> {
  try {
    const res = await api.article.list({
      category: params?.category,
      audience: params?.audience
    })
    if (hasNewFields(res)) {
      let list = res as Article[]
      if (params?.lengthType && params.lengthType !== 'all') {
        list = list.filter(a => a.lengthType === params.lengthType)
      }
      if (params?.keyword) {
        const k = params.keyword.toLowerCase()
        list = list.filter(a =>
          (a.title || '').toLowerCase().includes(k) ||
          (a.summary || '').toLowerCase().includes(k) ||
          (a.topic || '').toLowerCase().includes(k)
        )
      }
      return list
    }
  } catch (e) {
    console.warn('文章列表后端不可用，回退 mock', e)
  }
  // 回退 mock
  return MOCK_ARTICLES.filter(a => {
    if (params?.category && a.category !== params.category) return false
    if (params?.audience && a.audience !== params.audience) return false
    if (params?.lengthType && params.lengthType !== 'all' && a.lengthType !== params.lengthType) return false
    if (params?.keyword) {
      const k = params.keyword.toLowerCase()
      if (!(a.title.toLowerCase().includes(k) || (a.summary || '').toLowerCase().includes(k) || (a.topic || '').toLowerCase().includes(k))) return false
    }
    return true
  })
}

/**
 * 拉取文章详情：优先后端，后端无此文章或缺新字段时回退 mock（按 id）。
 */
export async function fetchArticleDetail(id: number): Promise<Article | null> {
  try {
    const res = await api.article.detail(id)
    if (res && (res as any).lengthType) return res as Article
    // 后端有文章但缺新字段 → 用 mock 同 id 兜底，保证三档篇幅可切换
    const mock = MOCK_ARTICLES.find(a => a.id === id)
    if (mock) return mock
    // mock 也没有 → 返回后端原始数据（至少能展示）
    return res ? { ...(res as any), lengthType: 'medium' } : null
  } catch (e) {
    console.warn('文章详情后端不可用，回退 mock', e)
    return MOCK_ARTICLES.find(a => a.id === id) || null
  }
}

/** 解析参考文献 JSON */
export function parseSources(sourcesJson?: string): string[] {
  try {
    if (!sourcesJson) return []
    const arr = typeof sourcesJson === 'string' ? JSON.parse(sourcesJson) : sourcesJson
    return Array.isArray(arr) ? arr : []
  } catch {
    return []
  }
}

/**
 * AI 生成科普文章：调用后端 /articles/generate 端点。
 * 后端会调 AI 生成母稿 → 拆分三版 → 校验 → 入库，返回三篇文章 + 质量评分。
 */
export async function generateArticle(topic: string, persona?: string): Promise<{
  code: number
  message: string
  qualityScore: number
  passed: boolean
  errors: string[]
  topicGroupId: string
  articles: Article[]
}> {
  const res = await api.article.generate(topic, persona)
  // 响应拦截器已剥离 data，res 即为后端返回的 Map
  return res as any
}

/**
 * 获取同主题不同篇幅的相关文章：优先后端，失败回退 mock。
 */
export async function fetchRelatedArticles(topicGroupId: string, excludeId?: number): Promise<Article[]> {
  try {
    const res = await api.article.related(topicGroupId, excludeId)
    if (Array.isArray(res) && res.length > 0) return res as Article[]
  } catch (e) {
    console.warn('相关文章后端不可用，回退 mock', e)
  }
  // 回退 mock
  return MOCK_ARTICLES.filter(a => a.topicGroupId === topicGroupId && a.id !== excludeId)
}
