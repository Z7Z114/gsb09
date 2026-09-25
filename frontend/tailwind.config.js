/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'wood': {
          50: '#fdf8f3',
          100: '#f5e6d3',
          200: '#e8ccaa',
          300: '#d4a574',
          400: '#c4844a',
          500: '#a0522d',
          600: '#8B4513',
          700: '#6b3410',
          800: '#5a2c0e',
          900: '#4a230b',
        },
        'parchment': {
          50: '#fffbf0',
          100: '#fff3d6',
          200: '#ffe8ad',
          300: '#ffd87a',
          400: '#ffc447',
          500: '#f5b321',
        }
      },
      fontFamily: {
        'serif': ['Noto Serif SC', 'serif'],
      },
    },
  },
  plugins: [],
}
