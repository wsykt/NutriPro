<template>
  <div class="edu-layout">
    <!-- ========== 左侧文章目录 ========== -->
    <aside class="edu-sidebar">
      <div class="edu-sidebar-head">
        <h2 class="edu-title">健康科普</h2>
        <p class="edu-subtitle">Knowledge Hub</p>
      </div>

      <!-- 分类筛选 -->
      <div class="edu-filter">
        <button
          v-for="cat in categories"
          :key="cat"
          class="edu-tag"
          :class="{ active: activeCategory === cat }"
          @click="activeCategory = cat"
        >{{ cat }}</button>
      </div>

      <!-- 文章列表 -->
      <div class="edu-list">
        <div
          v-for="article in filteredArticles"
          :key="article.id"
          class="edu-list-item"
          :class="{ active: selectedId === article.id }"
          @click="selectArticle(article)"
        >
          <div class="edu-item-icon" :style="{ background: article.bgColor }">
            <component :is="article.icon" class="w-4 h-4" :style="{ color: article.color }" />
          </div>
          <div class="edu-item-body">
            <p class="edu-item-title">{{ article.title }}</p>
            <div class="edu-item-meta">
              <span class="edu-item-cat">{{ article.category }}</span>
              <span class="edu-item-date">{{ article.date }}</span>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- ========== 右侧文章阅读区 ========== -->
    <main class="edu-reader">
      <template v-if="currentArticle">
        <!-- 面包屑 -->
        <div class="edu-breadcrumb">
          <span>{{ currentArticle.category }}</span>
          <ChevronRight class="w-3.5 h-3.5" />
          <span>健康科普</span>
        </div>

        <!-- 文章头部 -->
        <header class="edu-article-header">
          <div class="edu-cover" :style="{ background: currentArticle.bgColor }">
            <component :is="currentArticle.icon" class="w-14 h-14" :style="{ color: currentArticle.color }" />
          </div>
          <div class="edu-article-meta">
            <span class="edu-badge" :style="{ background: currentArticle.bgColor, color: currentArticle.color }">{{ currentArticle.category }}</span>
            <span class="edu-dot">·</span>
            <span class="edu-meta-item">{{ currentArticle.date }}</span>
            <span class="edu-dot">·</span>
            <span class="edu-meta-item">阅读约 {{ currentArticle.readTime }} 分钟</span>
          </div>
          <h1 class="edu-article-title">{{ currentArticle.title }}</h1>
          <p class="edu-article-summary">{{ currentArticle.summary }}</p>
        </header>

        <!-- 分割线 -->
        <div class="edu-divider">
          <div class="edu-divider-line"></div>
          <Leaf class="edu-divider-icon" />
          <div class="edu-divider-line"></div>
        </div>

        <!-- 文章正文 -->
        <article class="edu-article-body">
          <section
            v-for="(section, idx) in currentArticle.sections"
            :key="idx"
            class="edu-section"
          >
            <h2 v-if="section.heading" class="edu-section-title">
              <span class="edu-section-num">{{ idx + 1 }}</span>
              {{ section.heading }}
            </h2>
            <p
              v-for="(para, pIdx) in section.paragraphs"
              :key="pIdx"
              class="edu-paragraph"
              :class="{ 'edu-quote': para.startsWith('>') }"
            >{{ para.startsWith('>') ? para.slice(1) : para }}</p>
            <ul v-if="section.bullets?.length" class="edu-bullet-list">
              <li v-for="(bullet, bIdx) in section.bullets" :key="bIdx">{{ bullet }}</li>
            </ul>
          </section>

          <!-- 小贴士 -->
          <div class="edu-tip-box" v-if="currentArticle.tips?.length">
            <div class="edu-tip-head">
              <Lightbulb class="w-4 h-4" />
              <span>健康小贴士</span>
            </div>
            <ul class="edu-tip-list">
              <li v-for="(tip, tIdx) in currentArticle.tips" :key="tIdx">{{ tip }}</li>
            </ul>
          </div>
        </article>

        <!-- 文章底部操作 -->
        <footer class="edu-article-footer">
          <button class="edu-foot-btn" @click="prevArticle" :disabled="currentIndex <= 0">
            <ChevronLeft class="w-4 h-4" />
            上一篇
          </button>
          <span class="edu-foot-center">{{ currentIndex + 1 }} / {{ filteredArticles.length }}</span>
          <button class="edu-foot-btn" @click="nextArticle" :disabled="currentIndex >= filteredArticles.length - 1">
            下一篇
            <ChevronRight class="w-4 h-4" />
          </button>
        </footer>
      </template>

      <!-- 空状态 -->
      <div v-else class="edu-empty">
        <BookOpen class="w-16 h-16 text-slate-300" />
        <p>请从左侧选择一篇科普文章开始阅读</p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, type Component } from 'vue'
import {
  UtensilsCrossed,
  Activity,
  Moon,
  Brain,
  Stethoscope,
  Flower2,
  Leaf,
  ChevronRight,
  ChevronLeft,
  Lightbulb,
  BookOpen
} from 'lucide-vue-next'

interface Article {
  id: number
  title: string
  summary: string
  icon: Component
  category: string
  date: string
  color: string
  bgColor: string
  readTime: number
  sections: { heading?: string; paragraphs: string[]; bullets?: string[] }[]
  tips?: string[]
}

const articles = ref<Article[]>([
  {
    id: 1,
    title: '合理饮食对健康的重要性',
    summary: '饮食是维持生命的基础，合理的饮食结构能够为身体提供充足的营养，预防多种疾病的发生。',
    icon: UtensilsCrossed,
    category: '饮食健康',
    date: '2024-01-15',
    color: '#ef4444',
    bgColor: 'rgba(239,68,68,0.1)',
    readTime: 6,
    sections: [
      {
        heading: '均衡饮食的基本原则',
        paragraphs: [
          '饮食是维持生命的基础，合理的饮食结构能够为身体提供充足的营养，预防多种疾病的发生。',
          '均衡饮食应包含碳水化合物、蛋白质、脂肪、维生素和矿物质等营养素。主食应粗细搭配，多吃杂粮和薯类，建议占每日总能量的 50%–65%。'
        ]
      },
      {
        heading: '各类营养素的摄入建议',
        paragraphs: [
          '蛋白质来源应多样化，包括鱼、肉、蛋、奶和豆类。每天摄入适量的优质蛋白质有助于维持肌肉和免疫系统健康，推荐摄入量为每公斤体重 1.0–1.2 克。',
          '蔬菜和水果富含维生素、矿物质和膳食纤维，建议每天摄入 500 克以上蔬菜和 200–350 克水果，其中深色蔬菜应占一半以上。'
        ],
        bullets: [
          '主食：粗细搭配，适量增加全谷物',
          '蛋白质：鱼禽肉蛋奶豆，每天 120–200 克',
          '蔬菜：每天 500 克，深色蔬菜占一半',
          '水果：每天 200–350 克'
        ]
      },
      {
        heading: '需要避免的饮食习惯',
        paragraphs: [
          '减少高油、高盐、高糖食物的摄入，避免过量饮酒和吸烟，这些不良习惯会增加心血管疾病和癌症的风险。',
          '养成规律进餐的习惯，定时定量，避免暴饮暴食。晚餐不宜过晚、过饱，睡前 3 小时应避免进食。'
        ]
      }
    ],
    tips: [
      '每天喝 1500–2000 毫升水，保持身体水分平衡',
      '烹饪方式以蒸、煮、炖、凉拌为主，减少煎炸',
      '每周至少吃 2 次深海鱼，补充 Omega-3 脂肪酸'
    ]
  },
  {
    id: 2,
    title: '适量运动的益处',
    summary: '运动不仅能帮助控制体重，还能增强心肺功能，改善睡眠质量，提高心理健康水平。',
    icon: Activity,
    category: '运动健康',
    date: '2024-01-12',
    color: '#10b981',
    bgColor: 'rgba(16,185,129,0.1)',
    readTime: 5,
    sections: [
      {
        heading: '运动对身体的益处',
        paragraphs: [
          '运动不仅能帮助控制体重，还能增强心肺功能，改善睡眠质量，提高心理健康水平。',
          '有氧运动如快走、慢跑、游泳等能够增强心肺功能，提高身体的耐力和免疫力，同时促进内啡肽分泌，改善情绪。'
        ]
      },
      {
        heading: '推荐的运动方案',
        paragraphs: [
          '力量训练如举铁、俯卧撑、仰卧起坐能够增加肌肉量，提高基础代谢率，帮助维持健康体重。每周建议进行 2–3 次力量训练，重点锻炼大肌群。',
          '建议每周进行至少 150 分钟的中等强度有氧运动，或 75 分钟的高强度有氧运动，并结合 2–3 次力量训练，形成"有氧 + 力量"的综合训练模式。'
        ],
        bullets: [
          '快走/慢跑：每周 5 次，每次 30 分钟',
          '力量训练：每周 2–3 次，间隔休息',
          '柔韧性训练：每日 10–15 分钟拉伸',
          '避免久坐：每小时起身活动 5 分钟'
        ]
      },
      {
        heading: '运动注意事项',
        paragraphs: [
          '运动前后要注意热身和拉伸，避免受伤。热身 5–10 分钟，拉伸 5–10 分钟。',
          '运动时要适量饮水，保持身体水分平衡。初学者应循序渐进，避免突然进行高强度训练。'
        ]
      }
    ],
    tips: [
      '空腹运动燃脂效果更好，但不适合糖尿病患者',
      '运动时心率保持在（220-年龄）×60%-70% 区间',
      '运动后 30 分钟内补充蛋白质和碳水，促进恢复'
    ]
  },
  {
    id: 3,
    title: '如何保持良好的睡眠质量',
    summary: '睡眠是身体修复和充电的重要过程，良好的睡眠质量对身心健康至关重要。',
    icon: Moon,
    category: '生活方式',
    date: '2024-01-10',
    color: '#6366f1',
    bgColor: 'rgba(99,102,241,0.1)',
    readTime: 5,
    sections: [
      {
        heading: '睡眠与健康的关系',
        paragraphs: [
          '睡眠是身体修复和充电的重要过程，良好的睡眠质量对身心健康至关重要。睡眠不足会影响免疫系统、代谢功能和认知能力，增加多种疾病的风险。',
          '成年人一般需要 7–9 小时的睡眠时间，青少年需要 8–10 小时，儿童需要 10–12 小时。长期睡眠不足 6 小时会增加心血管疾病、糖尿病和肥胖的风险。'
        ]
      },
      {
        heading: '改善睡眠的方法',
        paragraphs: [
          '保持规律的作息时间，每天在同一时间上床睡觉和起床，有助于建立稳定的生物钟。即使周末也不要相差超过 1 小时。',
          '睡前避免使用电子设备，保持卧室安静、黑暗和凉爽，创造一个舒适的睡眠环境。卧室温度建议在 18–22℃。'
        ],
        bullets: [
          '固定作息：每天同一时间睡觉和起床',
          '睡前 1 小时：关闭电子设备，蓝光会抑制褪黑素',
          '卧室环境：黑暗、安静、凉爽（18–22℃）',
          '避免刺激：睡前 4 小时不饮用咖啡因'
        ]
      },
      {
        heading: '建立睡前仪式',
        paragraphs: [
          '睡前可以进行放松活动，如阅读、听音乐、冥想等，避免剧烈运动和刺激性活动。',
          '推荐睡前 30 分钟进行温水浴（38–40℃），有助于身体核心温度下降，触发困意。'
        ]
      }
    ],
    tips: [
      '如果 20 分钟内无法入睡，起身阅读无聊的书，有睡意再回床',
      '下午 2 点之后避免饮用咖啡、茶等含咖啡因饮料',
      '每天晒 30 分钟自然光，帮助调节生物钟'
    ]
  },
  {
    id: 4,
    title: '心理健康与压力管理',
    summary: '心理健康是整体健康的重要组成部分，学会管理压力对维持身心健康至关重要。',
    icon: Brain,
    category: '心理健康',
    date: '2024-01-08',
    color: '#a855f7',
    bgColor: 'rgba(168,85,247,0.1)',
    readTime: 7,
    sections: [
      {
        heading: '认识心理压力',
        paragraphs: [
          '心理健康是整体健康的重要组成部分，学会管理压力对维持身心健康至关重要。',
          '长期处于高压状态会导致焦虑、抑郁等心理问题，还会影响身体健康，增加心血管疾病的风险。持续的压力会导致皮质醇水平升高，影响免疫系统、代谢和睡眠。'
        ]
      },
      {
        heading: '日常减压方法',
        paragraphs: [
          '学会识别和表达自己的情绪，与家人和朋友保持良好的沟通，寻求社会支持。倾诉是最好的心理疗愈方式之一。',
          '培养兴趣爱好，如听音乐、画画、旅游等，能够帮助放松身心，缓解压力。定期安排"愉悦活动"是心理保健的重要手段。'
        ],
        bullets: [
          '深呼吸：4-7-8 呼吸法（吸 4 秒、屏 7 秒、呼 8 秒）',
          '正念冥想：每天 10 分钟，专注当下',
          '身体活动：快走、慢跑释放压力激素',
          '社交连接：与朋友家人面对面交流'
        ]
      },
      {
        heading: '何时寻求专业帮助',
        paragraphs: [
          '如果感到持续的焦虑或抑郁，应及时寻求专业心理咨询师的帮助。心理健康问题与身体疾病一样，需要专业治疗。',
          '当睡眠、食欲、情绪持续异常超过两周，且影响正常生活时，建议前往正规医疗机构的精神心理科就诊。'
        ]
      }
    ],
    tips: [
      '每天记录三件感恩的小事，培养积极心态',
      '允许自己"无所事事"，休息也是生产力',
      '设定健康边界，学会对不合理的要求说"不"'
    ]
  },
  {
    id: 5,
    title: '常见慢性病的预防',
    summary: '随着生活方式的改变，慢性病已成为威胁人类健康的主要因素，了解预防方法非常重要。',
    icon: Stethoscope,
    category: '疾病预防',
    date: '2024-01-05',
    color: '#0ea5e9',
    bgColor: 'rgba(14,165,233,0.1)',
    readTime: 8,
    sections: [
      {
        heading: '高血压的预防',
        paragraphs: [
          '高血压是最常见的慢性病之一，被称为"无声的杀手"。保持低盐饮食，控制体重，定期监测血压，遵医嘱服用药物。',
          '成人每日食盐摄入量应不超过 5 克（约一个啤酒瓶盖），减少腌制、酱制食品的摄入。'
        ]
      },
      {
        heading: '糖尿病的预防',
        paragraphs: [
          '糖尿病：控制饮食，适量运动，定期检测血糖，避免高糖高脂食物。',
          '建议 40 岁以上人群每年进行一次空腹血糖或糖化血红蛋白检测，早发现、早干预。'
        ],
        bullets: [
          '控制体重：BMI 保持在 18.5–23.9',
          '规律运动：每周 150 分钟中等强度有氧',
          '健康饮食：低升糖指数（GI）食物为主',
          '定期监测：每年 1 次血糖检测'
        ]
      },
      {
        heading: '心血管疾病与癌症',
        paragraphs: [
          '心血管疾病：戒烟限酒，保持健康饮食，定期进行体检，及时治疗高血压和高血脂。',
          '癌症：保持健康生活方式，定期进行癌症筛查，避免接触有害物质。常见筛查包括低剂量 CT（肺癌）、胃镜（胃癌）、肠镜（肠癌）等。'
        ]
      }
    ],
    tips: [
      '每年进行一次全面体检，包括血脂、血糖、肝肾功能',
      '接种相关疫苗：乙肝、HPV、流感等',
      '戒烟限酒，烟草是多种癌症的明确危险因素'
    ]
  },
  {
    id: 6,
    title: '春季养生指南',
    summary: '春季是万物复苏的季节，也是养生的好时机，合理的养生方法能够帮助身体适应季节变化。',
    icon: Flower2,
    category: '季节养生',
    date: '2024-01-03',
    color: '#f59e0b',
    bgColor: 'rgba(245,158,11,0.1)',
    readTime: 6,
    sections: [
      {
        heading: '春季养生总原则',
        paragraphs: [
          '春季是万物复苏的季节，也是养生的好时机，合理的养生方法能够帮助身体适应季节变化。',
          '中医认为春属木，通于肝。春季养生宜"升"不宜"降"，重在养肝护肝，应保持心情舒畅，多进行户外活动。'
        ]
      },
      {
        heading: '饮食与起居',
        paragraphs: [
          '饮食养生：多吃清淡易消化的食物，如春笋、菠菜、韭菜等春季时令蔬菜，少吃油腻辛辣食物。可适当食用芽菜、豆豉、薄荷等辛散之品。',
          '起居养生：春季阳气渐盛，应早睡早起，适当增加户外活动时间，接触大自然。"春三月，此谓发陈，天地俱生，万物以荣"。'
        ],
        bullets: [
          '宜食：春笋、菠菜、韭菜、香椿、豆芽',
          '少食：油腻、辛辣、生冷食物',
          '推荐：早睡早起，晨练以散步、八段锦为宜',
          '注意：防过敏，花粉季减少外出'
        ]
      },
      {
        heading: '情志与防病',
        paragraphs: [
          '情志养生：春季容易出现情绪波动，要保持心情舒畅，避免过度思虑和焦虑。可通过踏青、赏花、书法等方式调节情志。',
          '防病养生：春季是流感等传染病的高发期，要注意个人卫生，勤洗手，保持室内通风。过敏体质者应注意防护。'
        ]
      }
    ],
    tips: [
      '晨起一杯温水，可加少量柠檬或蜂蜜',
      '拍打肝经（大腿内侧）有助于疏肝理气',
      '外出踏青时注意防晒和防花粉过敏'
    ]
  }
])

const categories = ['全部', '饮食健康', '运动健康', '生活方式', '心理健康', '疾病预防', '季节养生']
const activeCategory = ref('全部')

const filteredArticles = computed(() => {
  if (activeCategory.value === '全部') return articles.value
  return articles.value.filter(a => a.category === activeCategory.value)
})

const selectedId = ref<number>(articles.value[0].id)
const currentArticle = computed(() => filteredArticles.value.find(a => a.id === selectedId.value) || null)
const currentIndex = computed(() => filteredArticles.value.findIndex(a => a.id === selectedId.value))

const selectArticle = (article: Article) => {
  selectedId.value = article.id
}

const prevArticle = () => {
  const idx = currentIndex.value
  if (idx > 0) selectedId.value = filteredArticles.value[idx - 1].id
}

const nextArticle = () => {
  const idx = currentIndex.value
  if (idx < filteredArticles.value.length - 1) selectedId.value = filteredArticles.value[idx + 1].id
}

onMounted(() => {
  if (filteredArticles.value.length > 0) {
    selectedId.value = filteredArticles.value[0].id
  }
})
</script>

<style scoped>
.edu-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 24px;
  min-height: calc(100vh - 120px);
}

/* ========== 左侧 ========== */
.edu-sidebar {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px 18px;
  border: 1px solid rgba(15, 23, 42, 0.05);
  display: flex;
  flex-direction: column;
  gap: 18px;
  position: sticky;
  top: 88px;
  align-self: start;
  max-height: calc(100vh - 120px);
  overflow: hidden;
}
.edu-sidebar-head {
  text-align: center;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
}
.edu-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  letter-spacing: -0.3px;
}
.edu-subtitle {
  font-size: 10px;
  color: #94a3b8;
  margin: 2px 0 0;
  letter-spacing: 2px;
  text-transform: uppercase;
}

/* 分类 */
.edu-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 4px;
}
.edu-tag {
  font-size: 11px;
  font-weight: 500;
  padding: 5px 11px;
  border-radius: 99px;
  background: #f1f5f9;
  color: #64748b;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}
.edu-tag:hover {
  background: #e2e8f0;
}
.edu-tag.active {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #fff;
  box-shadow: 0 3px 10px rgba(16, 185, 129, 0.25);
}

/* 文章列表 */
.edu-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-right: 6px;
}
.edu-list::-webkit-scrollbar {
  width: 4px;
}
.edu-list::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.edu-list-item {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}
.edu-list-item:hover {
  background: #f8fafc;
  border-color: rgba(15, 23, 42, 0.04);
}
.edu-list-item.active {
  background: linear-gradient(135deg, rgba(16,185,129,0.08) 0%, rgba(14,165,233,0.06) 100%);
  border-color: rgba(16, 185, 129, 0.18);
}

.edu-item-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.edu-item-body {
  flex: 1;
  min-width: 0;
}
.edu-item-title {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 3px;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.edu-item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
  color: #94a3b8;
}
.edu-item-cat {
  color: #10b981;
  font-weight: 500;
}

/* ========== 右侧阅读区 ========== */
.edu-reader {
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid rgba(15, 23, 42, 0.05);
  padding: 48px 56px;
  min-height: calc(100vh - 160px);
  animation: fadeSlideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}
@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.edu-breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 28px;
}

/* 文章头 */
.edu-article-header {
  margin-bottom: 28px;
}
.edu-cover {
  width: 72px;
  height: 72px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}
.edu-article-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.edu-badge {
  padding: 3px 10px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 11px;
}
.edu-dot {
  color: #cbd5e1;
}
.edu-meta-item {
  color: #94a3b8;
}
.edu-article-title {
  font-size: 30px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.3;
  margin: 0 0 14px;
  letter-spacing: -0.5px;
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
}
.edu-article-summary {
  font-size: 15px;
  color: #64748b;
  line-height: 1.7;
  margin: 0;
  padding: 16px 20px;
  background: #f8fafc;
  border-left: 3px solid #10b981;
  border-radius: 0 10px 10px 0;
}

/* 分割线 */
.edu-divider {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 28px 0;
}
.edu-divider-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(to right, transparent, rgba(15,23,42,0.12), transparent);
}
.edu-divider-icon {
  width: 18px;
  height: 18px;
  color: #10b981;
  opacity: 0.6;
}

/* 正文 */
.edu-article-body {
  font-size: 15px;
  line-height: 1.9;
  color: #334155;
}
.edu-section {
  margin-bottom: 28px;
}
.edu-section-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  letter-spacing: -0.3px;
}
.edu-section-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}
.edu-paragraph {
  margin: 0 0 16px;
  text-align: justify;
  text-indent: 2em;
  line-height: 1.9;
}
.edu-paragraph.edu-quote {
  background: linear-gradient(135deg, rgba(16,185,129,0.06), rgba(14,165,233,0.04));
  border-left: 3px solid #10b981;
  padding: 14px 20px;
  margin: 16px 0;
  border-radius: 0 10px 10px 0;
  color: #0f172a;
  font-style: italic;
  text-indent: 0;
}
.edu-bullet-list {
  margin: 12px 0 16px;
  padding: 16px 20px 16px 42px;
  background: #f8fafc;
  border-radius: 12px;
  list-style: disc;
}
.edu-bullet-list li {
  margin-bottom: 6px;
  line-height: 1.7;
  color: #334155;
}

/* 小贴士 */
.edu-tip-box {
  margin: 32px 0 8px;
  background: linear-gradient(135deg, rgba(245,158,11,0.08) 0%, rgba(251,191,36,0.04) 100%);
  border: 1px solid rgba(245, 158, 11, 0.18);
  border-radius: 14px;
  padding: 20px 24px;
}
.edu-tip-head {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #d97706;
  font-weight: 700;
  font-size: 14px;
  margin-bottom: 12px;
}
.edu-tip-list {
  margin: 0;
  padding-left: 20px;
}
.edu-tip-list li {
  font-size: 13.5px;
  line-height: 1.8;
  color: #78350f;
  margin-bottom: 6px;
}

/* 文章底部 */
.edu-article-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid rgba(15, 23, 42, 0.06);
}
.edu-foot-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
}
.edu-foot-btn:hover:not(:disabled) {
  background: #f1f5f9;
  color: #0f172a;
}
.edu-foot-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.edu-foot-center {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
}

/* 空状态 */
.edu-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: #94a3b8;
  gap: 12px;
  font-size: 14px;
}

/* 响应式 */
@media (max-width: 960px) {
  .edu-layout {
    grid-template-columns: 1fr;
  }
  .edu-sidebar {
    position: relative;
    top: 0;
    max-height: none;
  }
  .edu-reader {
    padding: 32px 24px;
  }
  .edu-article-title {
    font-size: 24px;
  }
}
</style>
