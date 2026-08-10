/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          'Inter', '-apple-system', 'BlinkMacSystemFont',
          'Segoe UI', 'Roboto',
          'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Microsoft YaHei UI',
          'Source Han Sans SC', 'Noto Sans CJK SC', 'WenQuanYi Micro Hei',
          'Helvetica Neue', 'Arial', 'sans-serif'
        ],
        inter: ['Inter', 'sans-serif'],
      },
      colors: {
        morandi: {
          gray: '#f4f5f7',
          soft: '#e8eaee',
          text: '#2d3748',
          lightText: '#718096',
          accent: '#43b086'
        }
      }
    },
  },
  plugins: [],
}
