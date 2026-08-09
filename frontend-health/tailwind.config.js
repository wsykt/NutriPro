/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
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
