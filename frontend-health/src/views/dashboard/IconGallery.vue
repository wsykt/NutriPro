<template>
  <div class="min-h-screen bg-morandi-bg/30">
    <div class="mx-auto max-w-[1280px] px-4 py-8 md:py-10">

      <!-- ============ 页头 ============ -->
      <header class="mb-8">
        <div class="flex items-center gap-2.5 mb-3">
          <span class="inline-flex items-center justify-center w-9 h-9 rounded-xl bg-morandi-accent/12 text-morandi-accent border border-morandi-accent/25">
            <Component :is="Icons.Palette" class="w-5 h-5" />
          </span>
          <h1 class="text-2xl md:text-[28px] font-bold text-morandi-text tracking-tight">图标库选型参考</h1>
        </div>
        <p class="text-[15px] text-morandi-lightText leading-relaxed max-w-3xl">
          基于项目当前使用的 <code class="px-1.5 py-0.5 rounded bg-morandi-gray text-morandi-text text-[13px]">lucide-vue-next@1.0.0</code>
          （共 1705 个图标），按本项目各功能场景筛选出 <strong class="text-morandi-text">{{ totalCount }}</strong> 个可适配图标，
          覆盖科普文章、身体指标、饮食录入、食材管理、周报可视化等模块。点击任意图标可复制组件名。
        </p>

        <!-- 搜索框 -->
        <div class="mt-5 relative max-w-md">
          <Component :is="Icons.Search" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-morandi-lightText" />
          <input
            v-model="keyword"
            type="text"
            placeholder="搜索图标名或用途（如：警告、血糖、图表）"
            class="w-full pl-9 pr-9 py-2.5 text-sm rounded-xl border border-morandi-soft/60 bg-white text-morandi-text placeholder:text-morandi-lightText/60 focus:outline-none focus:ring-2 focus:ring-morandi-accent/30 focus:border-morandi-accent/40 transition"
          />
          <button v-if="keyword" @click="keyword = ''" class="absolute right-3 top-1/2 -translate-y-1/2 text-morandi-lightText hover:text-morandi-text">
            <Component :is="Icons.X" class="w-4 h-4" />
          </button>
        </div>

        <!-- 统计 -->
        <div class="mt-4 flex flex-wrap gap-2 text-xs">
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white border border-morandi-soft/50 text-morandi-lightText">
            <Component :is="Icons.LayoutGrid" class="w-3.5 h-3.5" /> {{ categories.length }} 个分类
          </span>
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white border border-morandi-soft/50 text-morandi-lightText">
            <Component :is="Icons.CircleCheck" class="w-3.5 h-3.5 text-emerald-500" /> 已验证可用
          </span>
          <span v-if="keyword" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-morandi-accent/10 border border-morandi-accent/30 text-morandi-accent">
            匹配 {{ filteredTotal }} 个结果
          </span>
        </div>
      </header>

      <!-- ============ 分类导航（sticky） ============ -->
      <nav class="sticky top-0 z-20 -mx-4 px-4 py-3 mb-6 bg-morandi-bg/80 backdrop-blur-md border-b border-morandi-soft/40">
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="cat in categories"
            :key="cat.id"
            @click="scrollTo(cat.id)"
            :class="[
              'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all',
              activeCat === cat.id
                ? 'bg-morandi-accent text-white border-morandi-accent shadow-sm shadow-morandi-accent/20'
                : 'bg-white text-morandi-lightText border-morandi-soft/50 hover:text-morandi-text hover:border-morandi-accent/40'
            ]"
          >
            <Component :is="cat.icon" class="w-3.5 h-3.5" />
            {{ cat.short }}
            <span :class="['ml-0.5 px-1 rounded text-[10px]', activeCat === cat.id ? 'bg-white/25' : 'bg-morandi-gray text-morandi-lightText']">
              {{ cat.icons.length }}
            </span>
          </button>
        </div>
      </nav>

      <!-- ============ 分类内容 ============ -->
      <div ref="contentRef">
        <section
          v-for="cat in categories"
          :id="'cat-' + cat.id"
          :key="cat.id"
          :ref="el => setSectionRef(el as HTMLElement, cat.id)"
          class="mb-10 scroll-mt-20"
        >
          <div class="flex items-center gap-2.5 mb-1">
            <span class="inline-flex items-center justify-center w-7 h-7 rounded-lg bg-white border border-morandi-soft/50 text-morandi-accent">
              <Component :is="cat.icon" class="w-4 h-4" />
            </span>
            <h2 class="text-lg font-semibold text-morandi-text">{{ cat.title }}</h2>
          </div>
          <p class="text-[13px] text-morandi-lightText mb-4 ml-9">{{ cat.desc }}</p>

          <!-- 子分组标签（食材分类用） -->
          <div v-if="cat.subgroups" class="ml-9 mb-3 flex flex-wrap gap-2">
            <span
              v-for="(sg, i) in cat.subgroups"
              :key="i"
              class="text-[11px] px-2 py-0.5 rounded-full bg-morandi-gray/60 text-morandi-lightText border border-morandi-soft/40"
            >{{ sg }}</span>
          </div>

          <!-- 图标网格 -->
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            <div
              v-for="item in cat.icons"
              :key="cat.id + '-' + item.name"
              v-show="!keyword || matchSearch(item, cat)"
              @click="copyName(item.pascal)"
              class="group relative flex flex-col items-center gap-2 p-3 rounded-xl bg-white border border-morandi-soft/40 hover:border-morandi-accent/50 hover:shadow-md hover:shadow-morandi-accent/8 cursor-pointer transition-all"
            >
              <Component :is="item.c" class="w-7 h-7 text-morandi-text group-hover:text-morandi-accent transition-colors" />
              <div class="text-center w-full min-w-0">
                <p class="text-[11px] font-mono text-morandi-lightText truncate">{{ item.name }}</p>
                <p class="text-[10px] text-morandi-lightText/70 truncate mt-0.5">{{ item.use }}</p>
              </div>
              <!-- 复制提示 -->
              <span
                v-if="copied === item.pascal"
                class="absolute -top-2 -right-2 inline-flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500 text-white"
              >
                <Component :is="Icons.Check" class="w-3 h-3" />
              </span>
            </div>
          </div>
        </section>

        <!-- 空状态 -->
        <div v-if="filteredTotal === 0 && keyword" class="py-20 text-center">
          <Component :is="Icons.SearchX" class="w-12 h-12 mx-auto text-morandi-lightText/40 mb-3" />
          <p class="text-morandi-lightText">未找到匹配「{{ keyword }}」的图标</p>
        </div>
      </div>

      <!-- ============ 底部说明 ============ -->
      <footer class="mt-12 p-5 rounded-2xl bg-white border border-morandi-soft/40">
        <h3 class="flex items-center gap-2 text-sm font-semibold text-morandi-text mb-2">
          <Component :is="Icons.Lightbulb" class="w-4 h-4 text-amber-500" /> 使用说明
        </h3>
        <ul class="text-[13px] text-morandi-lightText space-y-1.5 leading-relaxed">
          <li>• 图标名为 <code class="px-1 rounded bg-morandi-gray text-morandi-text">kebab-case</code>，在 Vue 中以 <code class="px-1 rounded bg-morandi-gray text-morandi-text">PascalCase</code> 导入，如 <code class="px-1 rounded bg-morandi-gray text-morandi-text">import { HeartPulse } from 'lucide-vue-next'</code></li>
          <li>• 点击图标卡片可复制组件名（PascalCase），便于直接粘贴到 import 语句</li>
          <li>• 本页面仅列出与本项目相关的图标子集，完整列表见 <a href="https://lucide.dev/icons/" target="_blank" class="text-morandi-accent underline underline-offset-2">lucide.dev/icons</a></li>
          <li>• 项目已使用的旧名称别名（如 <code class="px-1 rounded bg-morandi-gray text-morandi-text">AlertTriangle</code>）仍兼容，新代码建议采用本页标准命名</li>
        </ul>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { Component } from 'vue'
import * as Icons from 'lucide-vue-next'

/* =================== 图标分类数据 =================== */
interface IconItem {
  c: Component
  name: string       // kebab-case
  pascal: string     // PascalCase 组件名
  use: string        // 适用场景
}
interface Category {
  id: string
  short: string
  title: string
  desc: string
  icon: Component
  subgroups?: string[]
  icons: IconItem[]
}

// 辅助：构造图标项
const I = (pascal: string, use: string): IconItem => {
  const c = (Icons as any)[pascal]
  const name = pascal
    .replace(/([A-Z])/g, (m, p, i) => (i ? '-' : '') + p.toLowerCase())
    .replace(/(\d+)/g, '-$1')
    .replace(/^-/, '')
  return { c, name, pascal, use }
}

const categories: Category[] = [
  {
    id: 'alert',
    short: '警告提示',
    title: '科普文章 · 警告与提示',
    desc: '用于标记注意事项、推荐做法、避免行为、风险警示等状态信息',
    icon: Icons.TriangleAlert,
    icons: [
      I('CircleAlert', '一般提示 / 注意事项'),
      I('TriangleAlert', '警告 / 需谨慎'),
      I('OctagonAlert', '严重警告 / 禁忌'),
      I('CircleX', '错误 / 应避免'),
      I('Ban', '禁止 / 不可食用'),
      I('ShieldAlert', '安全警示 / 风险提示'),
      I('ShieldCheck', '已验证 / 权威背书'),
      I('Siren', '紧急 / 高危提醒'),
      I('Lightbulb', '要点提示 / 小贴士'),
      I('Sparkles', '亮点 / 重点推荐'),
      I('CircleCheck', '正确 / 推荐做法'),
      I('CircleCheckBig', '强推荐 / 达标'),
      I('BadgeCheck', '认证 / 权威标记'),
      I('BadgeInfo', '信息说明 / 补充'),
      I('Flame', '热量 / 能量相关'),
      I('Zap', '快速 / 能量补充'),
    ],
  },
  {
    id: 'food',
    short: '食品营养',
    title: '科普文章 · 食品与营养',
    desc: '文章配图、食材示意、营养素图标，可用于卡片配图和段落标记',
    icon: Icons.Apple,
    icons: [
      I('Apple', '水果 / 通用食材'),
      I('Banana', '水果 / 钾元素'),
      I('Cherry', '水果 / 抗氧化'),
      I('Citrus', '柑橘类 / 维生素C'),
      I('Grape', '水果 / 多酚'),
      I('Carrot', '蔬菜 / 胡萝卜素'),
      I('Salad', '蔬菜沙拉 / 低卡'),
      I('Leaf', '绿叶菜 / 膳食纤维'),
      I('LeafyGreen', '深色蔬菜 / 营养'),
      I('Sprout', '豆芽 / 豆制品'),
      I('Beef', '红肉 / 蛋白质'),
      I('Drumstick', '禽肉 / 蛋白质'),
      I('Ham', '加工肉 / 限制摄入'),
      I('Fish', '水产 / 优质蛋白'),
      I('Shrimp', '水产 / 低脂'),
      I('Egg', '蛋类 / 全营养'),
      I('EggFried', '蛋类 / 烹饪蛋'),
      I('Milk', '奶类 / 钙质'),
      I('Wheat', '主食 / 全谷物'),
      I('WheatOff', '主食 / 无麸质'),
      I('Donut', '高糖食品 / 限制'),
      I('Cake', '甜点 / 限制'),
      I('Cookie', '零食 / 限制'),
      I('IceCreamBowl', '甜品 / 限制'),
    ],
  },
  {
    id: 'drink',
    short: '饮品类',
    title: '科普文章 · 饮品与液体',
    desc: '饮水、饮品、汤汁相关图标，可用于水分摄入、饮品建议场景',
    icon: Icons.Coffee,
    icons: [
      I('Coffee', '咖啡 / 提神饮品'),
      I('Wine', '酒类 / 限制'),
      I('Beer', '啤酒 / 限制'),
      I('GlassWater', '饮水 / 补水'),
      I('CupSoda', '含糖饮料 / 限制'),
      I('Soup', '汤类 / 流食'),
      I('BottleWine', '酒类 / 饮酒警示'),
      I('IceCreamCone', '冷饮甜品 / 限制'),
    ],
  },
  {
    id: 'medical',
    short: '医疗健康',
    title: '科普文章 · 医疗健康',
    desc: '疾病管理、医疗元素、生理指标相关图标，用于疾病科普与专业内容',
    icon: Icons.HeartPulse,
    icons: [
      I('Heart', '心脏 / 心血管'),
      I('HeartPulse', '心率 / 生命体征'),
      I('Stethoscope', '听诊 / 诊疗'),
      I('Microscope', '研究 / 循证'),
      I('Pill', '药物 / 补充剂'),
      I('PillBottle', '药瓶 / 保健品'),
      I('Tablets', '药片 / 用药'),
      I('Syringe', '注射 / 疫苗'),
      I('Bandage', '创伤 / 护理'),
      I('BriefcaseMedical', '急救 / 医疗包'),
      I('Hospital', '医院 / 就医'),
      I('Cross', '医疗 / 急救标识'),
      I('Dna', '基因 / 精准营养'),
      I('Brain', '大脑 / 神经'),
      I('Bone', '骨骼 / 骨质'),
      I('Thermometer', '体温 / 发热'),
    ],
  },
  {
    id: 'citation',
    short: '引用学术',
    title: '科普文章 · 引用与学术',
    desc: '参考文献、学术标记、外部链接，用于文献引用和权威来源标注',
    icon: Icons.FileText,
    icons: [
      I('FileText', '文档 / 文献'),
      I('TextQuote', '引用 / 引言'),
      I('ExternalLink', '外部链接 / 来源'),
      I('ScrollText', '卷轴 / 论文'),
      I('NotebookText', '笔记 / 记录'),
      I('BookText', '书籍 / 教材'),
      I('BookOpenText', '阅读 / 资料'),
      I('BookOpenCheck', '已读 / 已核实'),
      I('BookCheck', '已验证文献'),
      I('GraduationCap', '学术 / 研究'),
    ],
  },
  {
    id: 'debate',
    short: '争议对比',
    title: '科普文章 · 争议与对比',
    desc: '学术争议、方案对比、双重视角，用于综述文的争议焦点区块',
    icon: Icons.Scale,
    icons: [
      I('Scale', '权衡 / 平衡'),
      I('Scale3d', '多维对比'),
      I('GitCompareArrows', '对比 / 比较'),
      I('ArrowLeftRight', '双向 / 互换'),
      I('GitBranch', '分支 / 多方案'),
      I('Split', '分歧 / 分支观点'),
    ],
  },
  {
    id: 'metrics',
    short: '身体指标',
    title: '身体指标 · 录入与监测',
    desc: '体重、身高、血压、心率、体温、睡眠、运动等指标录入与展示',
    icon: Icons.Scale,
    icons: [
      I('Scale', '体重秤 / 体重'),
      I('Weight', '重量 / 体重记录'),
      I('Ruler', '身高 / 尺寸'),
      I('RulerDimensionLine', '精确测量 / 腰围'),
      I('Gauge', '仪表 / 血压'),
      I('CircleGauge', '圆形仪表 / 指标盘'),
      I('HeartPulse', '心率 / 脉搏'),
      I('Activity', '活动量 / 心电图'),
      I('Thermometer', '体温 / 基础体温'),
      I('ThermometerSun', '高温 / 发热'),
      I('Moon', '睡眠 / 夜间'),
      I('MoonStar', '睡眠质量 / 深睡'),
      I('BedDouble', '睡眠 / 卧床'),
      I('Dumbbell', '力量训练 / 运动'),
      I('BicepsFlexed', '肌肉 / 体脂率'),
      I('Footprints', '步数 / 步行'),
    ],
  },
  {
    id: 'diet-input',
    short: '饮食录入',
    title: '饮食录入 · 餐具与识别',
    desc: '餐次标记、餐具、拍照识别、语音录入等饮食记录工具',
    icon: Icons.UtensilsCrossed,
    icons: [
      I('UtensilsCrossed', '餐具 / 用餐'),
      I('ChefHat', '烹饪 / 厨房'),
      I('CookingPot', '锅具 / 烹饪'),
      I('CupSoda', '杯具 / 饮品份量'),
      I('GlassWater', '饮水量 / 补水'),
      I('Refrigerator', '冰箱 / 食材存储'),
      I('Microwave', '加热 / 加工'),
      I('Camera', '拍照识别 / 记录'),
      I('ImagePlus', '添加图片 / 上传'),
      I('ScanLine', '扫描识别 / 条码'),
      I('ScanBarcode', '条形码 / 商品识别'),
      I('Mic', '语音录入 / 口述'),
    ],
  },
  {
    id: 'ingredient',
    short: '食材分类',
    title: '食材管理 · 按食物类别',
    desc: '对应项目食材库 8 大分类（主食/肉蛋类/水产/蔬菜/水果/豆制品/奶类/油脂类）',
    icon: Icons.Carrot,
    subgroups: ['主食', '肉蛋类', '水产', '蔬菜', '水果', '豆制品', '奶类', '油脂类'],
    icons: [
      // 主食
      I('Wheat', '主食 · 全谷物'),
      I('WheatOff', '主食 · 精制谷物'),
      I('Sprout', '主食 · 杂豆'),
      // 肉蛋类
      I('Beef', '肉蛋类 · 红肉'),
      I('Drumstick', '肉蛋类 · 禽肉'),
      I('Ham', '肉蛋类 · 加工肉'),
      I('Egg', '肉蛋类 · 蛋类'),
      I('EggFried', '肉蛋类 · 烹饪蛋'),
      // 水产
      I('Fish', '水产 · 鱼类'),
      I('Shrimp', '水产 · 虾蟹'),
      I('Shell', '水产 · 贝类'),
      I('FishingHook', '水产 · 捕捞'),
      // 蔬菜
      I('Carrot', '蔬菜 · 根茎类'),
      I('Salad', '蔬菜 · 叶菜'),
      I('Leaf', '蔬菜 · 绿叶菜'),
      I('LeafyGreen', '蔬菜 · 深色蔬菜'),
      I('Soup', '蔬菜 · 汤羹'),
      // 水果
      I('Apple', '水果 · 仁果'),
      I('Banana', '水果 · 热带水果'),
      I('Cherry', '水果 · 核果'),
      I('Citrus', '水果 · 柑橘类'),
      I('Grape', '水果 · 浆果'),
      I('Nut', '水果 · 坚果'),
      // 豆制品
      I('Sprout', '豆制品 · 豆芽'),
      I('LeafyGreen', '豆制品 · 豆苗'),
      // 奶类
      I('Milk', '奶类 · 液态奶'),
      I('MilkOff', '奶类 · 无乳糖'),
      // 油脂类
      I('Droplet', '油脂 · 食用油'),
      I('Droplets', '油脂 · 液态脂肪'),
      I('FlaskConical', '油脂 · 营养分析'),
      I('Beaker', '油脂 · 实验量取'),
      I('TestTube', '油脂 · 微量取样'),
    ],
  },
  {
    id: 'chart',
    short: '图表类型',
    title: '周报可视化 · 图表类型',
    desc: '营养摄入、指标变化的图表展示，适配周报、月报的数据可视化需求',
    icon: Icons.ChartBar,
    icons: [
      I('ChartBar', '柱状图 / 对比'),
      I('ChartLine', '折线图 / 趋势'),
      I('ChartPie', '饼图 / 占比'),
      I('ChartArea', '面积图 / 累积'),
      I('ChartColumn', '柱状图 / 纵向'),
      I('ChartColumnStacked', '堆叠柱图 / 分类占比'),
      I('ChartSpline', '曲线图 / 平滑趋势'),
      I('ChartScatter', '散点图 / 相关性'),
      I('ChartNetwork', '网络图 / 关联'),
      I('ChartNoAxesCombined', '组合图 / 多维'),
    ],
  },
  {
    id: 'trend',
    short: '趋势统计',
    title: '周报可视化 · 趋势与统计',
    desc: '数值统计、趋势方向、百分比、计算等数据表达元素',
    icon: Icons.TrendingUp,
    icons: [
      I('TrendingUp', '上升趋势 / 改善'),
      I('TrendingDown', '下降趋势 / 减量'),
      I('TrendingUpDown', '波动 / 不稳定'),
      I('Sigma', '求和 / 总量'),
      I('Percent', '百分比 / 占比'),
      I('CirclePercent', '环形进度 / 达成率'),
      I('Hash', '编号 / 计数'),
      I('Calculator', '计算 / BMR'),
      I('Gauge', '仪表盘 / 指标'),
      I('CircleGauge', '环形指标 / 评分'),
    ],
  },
  {
    id: 'heatmap',
    short: '热力图日历',
    title: '周报可视化 · 热力图与日历',
    desc: '打卡热力图、周期日历、网格布局，适配周报/月报的活动记录展示',
    icon: Icons.Calendar,
    icons: [
      I('Calendar', '日历 / 日期'),
      I('CalendarDays', '多日历 / 月视图'),
      I('CalendarCheck', '打卡 / 已完成'),
      I('CalendarRange', '区间 / 周期'),
      I('CalendarClock', '定时 / 日程'),
      I('Grid2x2', '网格 / 热力格'),
      I('Grid3x3', '密度网格 / 热力图'),
      I('LayoutGrid', '网格布局 / 卡片'),
      I('Table2', '表格 / 数据表'),
      I('LayoutDashboard', '仪表盘 / 总览'),
    ],
  },
  {
    id: 'goal',
    short: '目标成就',
    title: '周报可视化 · 目标与成就',
    desc: '目标达成、徽章奖励、里程碑标记，用于激励和成就展示',
    icon: Icons.Target,
    icons: [
      I('Target', '目标 / 靶心'),
      I('Trophy', '奖杯 / 成就'),
      I('Medal', '奖牌 / 排名'),
      I('Award', '荣誉 / 勋章'),
      I('Star', '评分 / 收藏'),
      I('Crown', '皇冠 / 顶级'),
      I('Flag', '里程碑 / 标记'),
      I('Rocket', '冲刺 / 突破'),
      I('BadgeCheck', '徽章 / 达标'),
      I('Sparkles', '亮点 / 高光'),
    ],
  },
  {
    id: 'time',
    short: '时间周期',
    title: '周报可视化 · 时间与周期',
    desc: '时长、计时、周期循环，用于阅读时长、运动时长、周/月周期标记',
    icon: Icons.Clock,
    icons: [
      I('Clock', '时间 / 时长'),
      I('ClockFading', '倒计时 / 渐隐'),
      I('Timer', '计时器 / 秒表'),
      I('TimerReset', '重置 / 循环'),
      I('Hourglass', '沙漏 / 耗时'),
      I('AlarmClock', '闹钟 / 提醒'),
    ],
  },
]

/* =================== 搜索过滤 =================== */
const keyword = ref('')
const matchSearch = (item: IconItem, cat: Category) => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return true
  return (
    item.name.toLowerCase().includes(kw) ||
    item.pascal.toLowerCase().includes(kw) ||
    item.use.toLowerCase().includes(kw) ||
    cat.title.toLowerCase().includes(kw)
  )
}
const filteredTotal = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return totalCount.value
  return categories.reduce((sum, cat) => sum + cat.icons.filter(it => matchSearch(it, cat)).length, 0)
})

/* =================== 统计 =================== */
const totalCount = computed(() => categories.reduce((s, c) => s + c.icons.length, 0))

/* =================== 点击复制 =================== */
const copied = ref('')
let copyTimer: any = null
const copyName = async (pascal: string) => {
  try {
    await navigator.clipboard.writeText(pascal)
  } catch {
    // 兜底
    const ta = document.createElement('textarea')
    ta.value = pascal
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
  }
  copied.value = pascal
  clearTimeout(copyTimer)
  copyTimer = setTimeout(() => (copied.value = ''), 1200)
}

/* =================== 分类导航锚点 + 滚动高亮 =================== */
const activeCat = ref(categories[0].id)
const sectionRefs: Record<string, HTMLElement> = {}
const setSectionRef = (el: HTMLElement | null, id: string) => {
  if (el) sectionRefs[id] = el
}
const scrollTo = (id: string) => {
  const el = sectionRefs[id]
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
let observer: IntersectionObserver | null = null
onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          const id = (e.target as HTMLElement).id.replace('cat-', '')
          activeCat.value = id
        }
      })
    },
    { rootMargin: '-80px 0px -70% 0px', threshold: 0 }
  )
  Object.values(sectionRefs).forEach((el) => observer?.observe(el))
})
onUnmounted(() => observer?.disconnect())
</script>

<style scoped>
code {
  font-family: 'SF Mono', 'Fira Code', Consolas, monospace;
}
</style>
