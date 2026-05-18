/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0f0f0f',
        surface: '#1a1a1a',
        'surface-elevated': '#2a2a2a',
        primary: '#ffffff',
        secondary: '#a0a0a0',
        accent: '#e5a00d',
        border: '#333333',
        'score-high': '#4ade80',
        'score-mid': '#facc15',
        'score-low': '#9ca3af',
      },
    },
  },
  plugins: [],
}
