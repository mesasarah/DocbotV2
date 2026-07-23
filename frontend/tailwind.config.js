/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0B0C0F",
          900: "#13151A",
          800: "#1B1E25",
          700: "#262A33",
          600: "#343945",
          500: "#4A505E",
        },
        paper: {
          100: "#EDEDEF",
          200: "#C9CAD1",
          300: "#9A9CA8",
        },
        rose: {
          400: "#F17A98",
          500: "#E8577E",
          600: "#C7436A",
        },
        sage: {
          400: "#93B9A2",
          500: "#7FA894",
          600: "#5E8A72",
        },
        amber: {
          400: "#E6BB6A",
          500: "#D9A441",
        },
        crimson: {
          400: "#DB7373",
          500: "#C75454",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      animation: {
        breathe: "breathe 3s ease-in-out infinite",
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-up": "slideUp 0.25s ease-out",
      },
      keyframes: {
        breathe: {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.5", transform: "scale(0.85)" },
        },
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        slideUp: {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
