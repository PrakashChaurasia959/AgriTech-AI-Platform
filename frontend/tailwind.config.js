/** @type {import("tailwindcss").Config} */
export default {
  darkMode: "class",
  content: ["./index.html","./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#16A34A",
          50: "#F0FDF4", 100: "#DCFCE7", 200: "#BBF7D0", 300: "#86EFAC",
          400: "#4ADE80", 500: "#22C55E", 600: "#16A34A", 700: "#15803D",
          800: "#166534", 900: "#14532D", 950: "#052e16",
        },
        accent: { yellow: "#FACC15", orange: "#F97316", cyan: "#06B6D4", violet: "#7C3AED" },
        background: "#F0F4F8",
        surface: "#FFFFFF",
        "surface-dark": "#111827",
        "border-light": "#E2E8F0",
        "border-dark": "#374151",
      },
      fontFamily: { sans: ["Inter var","Inter","system-ui","sans-serif"] },
      backgroundImage: {
        "hero-gradient": "linear-gradient(135deg,#052e16 0%,#14532D 40%,#166534 70%,#15803D 100%)",
        "card-shine": "linear-gradient(135deg,rgba(255,255,255,0.15) 0%,rgba(255,255,255,0) 60%)",
        "glass": "linear-gradient(135deg,rgba(255,255,255,0.1) 0%,rgba(255,255,255,0.05) 100%)",
      },
      boxShadow: {
        "glow-green": "0 0 20px rgba(22,163,74,0.35)",
        "glow-sm": "0 0 10px rgba(22,163,74,0.2)",
        "card": "0 4px 24px -4px rgba(0,0,0,0.08),0 2px 8px -2px rgba(0,0,0,0.06)",
        "card-hover": "0 12px 40px -8px rgba(0,0,0,0.14),0 4px 16px -4px rgba(0,0,0,0.08)",
        "glass": "0 8px 32px rgba(0,0,0,0.12),inset 0 1px 0 rgba(255,255,255,0.15)",
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-out",
        "slide-up": "slideUp 0.4s ease-out",
        "slide-in-right": "slideInRight 0.3s ease-out",
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
        "shimmer": "shimmer 2s linear infinite",
        "float": "float 4s ease-in-out infinite",
        "spin-slow": "spin 8s linear infinite",
      },
      keyframes: {
        fadeIn: { "0%": {opacity:"0"}, "100%": {opacity:"1"} },
        slideUp: { "0%": {transform:"translateY(16px)",opacity:"0"}, "100%": {transform:"translateY(0)",opacity:"1"} },
        slideInRight: { "0%": {transform:"translateX(16px)",opacity:"0"}, "100%": {transform:"translateX(0)",opacity:"1"} },
        pulseGlow: { "0%,100%": {boxShadow:"0 0 8px rgba(22,163,74,0.3)"}, "50%": {boxShadow:"0 0 24px rgba(22,163,74,0.7)"} },
        shimmer: { "0%": {backgroundPosition:"-200% 0"}, "100%": {backgroundPosition:"200% 0"} },
        float: { "0%,100%": {transform:"translateY(0)"}, "50%": {transform:"translateY(-8px)"} },
      },
      backdropBlur: { xs: "2px" },
      transitionTimingFunction: { "smooth": "cubic-bezier(0.4,0,0.2,1)" },
    },
  },
  plugins: [],
}
