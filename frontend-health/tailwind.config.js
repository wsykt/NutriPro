/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        // 正文：优先系统中文无衬线（去除 Inter，符合"自然治愈"设计系统）
        sans: [
          'PingFang SC', 'HarmonyOS Sans SC', 'Hiragino Sans GB',
          'Microsoft YaHei', 'Microsoft YaHei UI',
          'Source Han Sans SC', 'Noto Sans CJK SC',
          '-apple-system', 'BlinkMacSystemFont', 'sans-serif'
        ],
        // 标题：衬线（杂志/编辑感，对应 demo 设计系统 DISPLAY 字体）
        display: [
          'Noto Serif SC', 'Source Han Serif SC', 'Songti SC',
          'STSong', 'SimSun', 'serif'
        ],
        serif: ['Noto Serif SC', 'Source Han Serif SC', 'Songti SC', 'serif'],
      },
      colors: {
        // 「自然治愈 · 有机现代」设计系统（open-design-demo/DESIGN.md）
        morandi: {
          gray: '#F7F5F0',        // 页面底色（暖米白）
          soft: '#F1EDE4',        // 次级面板/输入框底
          'soft-green': '#E4EDE7',// 主色淡底（标签/进度条底）
          text: '#1F2A24',        // 主文字（深墨绿黑）
          'text-2': '#4A5550',    // 次级文字
          lightText: '#8A928C',   // 弱化文字/占位
          accent: '#2F5D4A',      // 主色（墨绿）
          amber: '#E07A3F',       // 强调（琥珀橙）
          danger: '#C25E4C',      // 警示
          line: '#E7E2D8',        // 分隔线/描边
        }
      }
    },
  },
  plugins: [],
}
