/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#0b0d10",
        surface: {
          DEFAULT: "#161b26",
          dim: "#0b0d10",
          lowest: "#0d1017",
          low: "#121620",
          container: "#161b26",
          high: "#1e2536",
          highest: "#262f45",
          border: "#263044",
        },
        primary: {
          DEFAULT: "#14b8a6",
          light: "#2dd4bf",
          dark: "#0d9488",
          container: "rgba(20, 184, 166, 0.12)",
        },
        secondary: {
          DEFAULT: "#06b6d4",
          light: "#22d3ee",
          dark: "#0891b2",
        },
        normal: {
          DEFAULT: "#0d9488",
          text: "#2dd4bf",
        },
        elevated: {
          DEFAULT: "#f59e0b",
          container: "rgba(245, 158, 11, 0.12)",
        },
        critical: {
          DEFAULT: "#e11d48",
          container: "rgba(225, 29, 72, 0.12)",
        },
        outline: {
          DEFAULT: "#334155",
          muted: "#1e293b",
        },
        content: {
          primary: "#f8fafc",
          secondary: "#cbd5e1",
          muted: "#64748b",
        }
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
    },
  },
  plugins: [],
}
