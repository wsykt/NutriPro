import type { Component } from 'vue'
import {
  User,
  Activity,
  UtensilsCrossed,
  BookOpen,
  Apple,
  Plus,
  BarChart3,
  Search,
  Users,
  Bot,
  FileText,
  Dumbbell,
  HeartHandshake,
  ScrollText,
  Newspaper,
  ChefHat
} from 'lucide-vue-next'

export interface Theme {
  primary: string
}

export interface Level2Menu {
  key: string
  label: string
  desc: string
  icon: Component
  route: string
}

export interface Level1Menu {
  key: Level1Key
  label: string
  description: string
  icon: Component
  theme: Theme
  children: Level2Menu[]
}

export type Level1Key = 'user' | 'food' | 'recipe' | 'health' | 'ai'

export const level1Map: Record<Level1Key, Level1Menu> = {
  user: {
    key: 'user',
    label: '用户中心',
    description: '个人档案、身体指标与健康历史',
    icon: User,
    theme: { primary: '#2F5D4A' },
    children: [
      {
        key: 'profile',
        label: '个人中心',
        desc: '管理账号信息、基础资料、人群类型',
        icon: User,
        route: '/dashboard/profile'
      },
      {
        key: 'metrics-history',
        label: '身体指标历史',
        desc: '查看身高体重血糖血压等指标的长期变化趋势',
        icon: Activity,
        route: '/dashboard/metrics-history'
      },
      {
        key: 'health-history',
        label: '健康档案历史',
        desc: '记录和追踪过往疾病、过敏、用药等历史档案',
        icon: FileText,
        route: '/dashboard/health-history'
      },
      {
        key: 'family-relation',
        label: '亲属关系管理',
        desc: '添加管理监护的家人信息，一键切换操作身份',
        icon: HeartHandshake,
        route: '/dashboard/family-relation'
      }
    ]
  },
  food: {
    key: 'food',
    label: '饮食管理',
    description: '食物录入、营养分析与家庭代录入',
    icon: UtensilsCrossed,
    theme: { primary: '#f59e0b' },
    children: [
      {
        key: 'food-input',
        label: '录入饮食',
        desc: '记录每一餐的食物摄入，自动计算营养成分',
        icon: Apple,
        route: '/dashboard/food-input'
      },
      {
        key: 'food-add',
        label: '添加食材',
        desc: '补充食材库中缺失的自定义食材与营养数据',
        icon: Plus,
        route: '/dashboard/food-add'
      },
      {
        key: 'nutrition',
        label: '营养分析',
        desc: '每日/每周宏量与微量营养素摄入的可视化分析',
        icon: BarChart3,
        route: '/dashboard/nutrition'
      },
      {
        key: 'food-search',
        label: '食物搜索',
        desc: '查询营养素、GI值、嘌呤、常见食材营养数据',
        icon: Search,
        route: '/dashboard/food-search'
      },
      {
        key: 'family-input',
        label: '亲属代录入饮食',
        desc: '为被监护的家人/老人/儿童代录入每日饮食',
        icon: Users,
        route: '/dashboard/family-input'
      }
    ]
  },
  recipe: {
    key: 'recipe',
    label: '菜谱管理',
    description: '菜谱浏览、收藏与个人饮食档案',
    icon: ChefHat,
    theme: { primary: '#ef4444' },
    children: [
      {
        key: 'recipe-library',
        label: '菜谱库',
        desc: '搜索、浏览、收藏健康菜谱，支持AI生成推荐',
        icon: BookOpen,
        route: '/dashboard/recipe-library'
      },
      {
        key: 'dietary-profile',
        label: '饮食档案管理',
        desc: '长期饮食模式回顾与个性化建议',
        icon: ScrollText,
        route: '/dashboard/dietary-profile'
      }
    ]
  },
  health: {
    key: 'health',
    label: '健康生活',
    description: '健康报告、运动记录',
    icon: Activity,
    theme: { primary: '#3b82f6' },
    children: [
      {
        key: 'health-report',
        label: '健康报告',
        desc: '个人健康综合评估报告与改进建议',
        icon: FileText,
        route: '/dashboard/health-report'
      },
      {
        key: 'muscle-chart',
        label: '运动记录',
        desc: '记录训练动作、训练部位与运动进度',
        icon: Dumbbell,
        route: '/dashboard/muscle-chart'
      }
    ]
  },
  ai: {
    key: 'ai',
    label: 'AI功能',
    description: 'AI健康咨询与科普文章阅读',
    icon: Bot,
    theme: { primary: '#8b5cf6' },
    children: [
      {
        key: 'ai-consult',
        label: 'AI健康咨询',
        desc: '智能对话解答饮食营养问题，含营养分析与周报',
        icon: Bot,
        route: '/dashboard/ai-consult'
      },
      {
        key: 'articles',
        label: '科普文章',
        desc: 'AI生成的营养科普文章，每主题三档篇幅可选',
        icon: Newspaper,
        route: '/dashboard/articles'
      }
    ]
  }
}
