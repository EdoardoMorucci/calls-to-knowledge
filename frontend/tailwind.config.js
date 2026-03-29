/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          900: '#0A0A0B',
          800: '#111113',
          700: '#161618',
          600: '#1E1E22',
          500: '#2A2A30',
          400: '#3D3D45',
        },
        stone: {
          primary: '#F0EFE8',
          secondary: '#9B9AA4',
          muted: '#4A4A52',
        },
        amber: {
          bright: '#C8963E',
          dim: '#8B6828',
          glow: 'rgba(200,150,62,0.15)',
        },
        signal: {
          rec: '#D94F35',
          proc: '#C8963E',
          done: '#3A9B66',
          error: '#7A3F3F',
        },
      },
      fontFamily: {
        display: ['"DM Serif Display"', 'Georgia', 'serif'],
        body: ['"DM Sans"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Courier New"', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp: { from: { opacity: '0', transform: 'translateY(6px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
      },
    },
  },
  plugins: [],
}
