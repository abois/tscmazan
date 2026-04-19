/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './**/templates/**/*.html',
    './**/*.py',
    './tscmazan/static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        bleu: {
          50: '#eef4fb',
          100: '#d4e4f7',
          200: '#a9c9ef',
          300: '#6fa5e3',
          400: '#3b80d1',
          500: '#2057b2',
          600: '#1a4690',
          700: '#15376f',
          800: '#0f2750',
          900: '#0a1a35',
          950: '#060f1f',
        },
        or: {
          50: '#fefaec',
          100: '#fdf0c8',
          200: '#fbe08d',
          300: '#f9cc52',
          400: '#f5b820',
          500: '#d4960a',
          600: '#a87308',
          700: '#7d540b',
          800: '#5e4010',
          900: '#3e2b0e',
        },
        sable: {
          50: '#faf8f5',
          100: '#f2ede6',
          200: '#e5dcd0',
          300: '#d2c4b0',
        },
      },
      fontFamily: {
        display: ['"Bebas Neue"', 'system-ui', 'sans-serif'],
        body: ['"DM Sans"', 'system-ui', 'sans-serif'],
      },
      keyframes: {
        slideUp: {
          from: { opacity: '0', transform: 'translateY(24px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'slide-up': 'slideUp 0.7s ease-out forwards',
      },
    },
  },
  plugins: [],
};
