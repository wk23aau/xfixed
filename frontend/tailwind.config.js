/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    // Match root files explicitly to avoid traversing node_modules
    "./*.{js,ts,jsx,tsx}",
    // Match potential subdirectories if added later
    "./components/**/*.{js,ts,jsx,tsx}",
    "./pages/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        background: '#09090b',
        surface: '#18181b',
        surfaceHighlight: '#27272a',
        primary: '#10b981',
        primaryDim: 'rgba(16, 185, 129, 0.1)',
        accent: '#3b82f6',
        text: '#f4f4f5',
        textDim: '#a1a1aa',
        border: '#3f3f46',
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        sans: ['ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}
