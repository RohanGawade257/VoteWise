/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#1E3A5F",
        secondary: "#2563EB",
        background: "#F8FAFC",
        surface: "#FFFFFF",
        border: "#E2E8F0",
        text: "#1E293B",
        muted: "#64748B",
        success: "#16A34A",
        warning: "#D97706",
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
