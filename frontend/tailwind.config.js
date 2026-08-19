/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0F172A', // Slate 900
        surface: '#1E293B',    // Slate 800
        border: '#334155',     // Slate 700
        primary: '#3B82F6',    // Blue 500
        primaryHover: '#2563EB',// Blue 600
        text: '#F8FAFC',       // Slate 50
        textMuted: '#94A3B8',  // Slate 400
        success: '#10B981',    // Emerald 500
        warning: '#F59E0B',    // Amber 500
        error: '#EF4444',      // Red 500
      }
    },
  },
  plugins: [],
}
