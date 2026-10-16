import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#DD614C",
          foreground: "#FFFFFF",
        },
        secondary: {
          DEFAULT: "#DAA144",
          foreground: "#111827",
        },
        text: "#111827",
        surface: "#FFFFFF",
        success: "#16A34A",
        warning: "#D97706",
        danger: "#DC2626",
        neutral: "#FFFFFF",
      },
      fontFamily: {
        sans: ["var(--font-darker-grotesque)", "system-ui", "sans-serif"],
        persian: ["var(--font-vazirmatn)", "system-ui", "sans-serif"],
        display: ["var(--font-darker-grotesque)", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"],
      },
      fontWeight: {
        thin: "100",
        extralight: "200",
        light: "300",
        normal: "400",
        medium: "500",
        semibold: "600",
        bold: "700",
        extrabold: "800",
        black: "900",
      },
      spacing: {
        "1": "4px",
        "2": "8px",
        "3": "12px",
        "4": "16px",
        "5": "20px",
        "6": "24px",
        "7": "28px",
        "8": "32px",
        "10": "40px",
        "12": "48px",
        "16": "64px",
        "20": "80px",
        "24": "96px",
      },
      borderRadius: {
        none: "0",
        "none-lg": "0",
        "none-xl": "0",
        "none-2xl": "0",
        "none-3xl": "0",
      },
      fontSize: {
        "display-xl": ["clamp(3rem, 8vw, 5rem)", { lineHeight: "1.1", letterSpacing: "-0.02em", fontWeight: "700" }],
        "display-lg": ["clamp(2.5rem, 6vw, 4rem)", { lineHeight: "1.15", letterSpacing: "-0.02em", fontWeight: "700" }],
        "display-md": ["clamp(2rem, 5vw, 3rem)", { lineHeight: "1.2", letterSpacing: "-0.01em", fontWeight: "600" }],
        "display-sm": ["clamp(1.5rem, 4vw, 2rem)", { lineHeight: "1.25", letterSpacing: "-0.01em", fontWeight: "600" }],
        "heading-xl": ["clamp(1.75rem, 4vw, 2.5rem)", { lineHeight: "1.3", letterSpacing: "0", fontWeight: "600" }],
        "heading-lg": ["clamp(1.5rem, 3vw, 2rem)", { lineHeight: "1.3", letterSpacing: "0", fontWeight: "600" }],
        "heading-md": ["clamp(1.25rem, 2.5vw, 1.5rem)", { lineHeight: "1.4", letterSpacing: "0", fontWeight: "600" }],
        "heading-sm": ["clamp(1.125rem, 2vw, 1.25rem)", { lineHeight: "1.4", letterSpacing: "0", fontWeight: "600" }],
        "body-lg": ["1.125rem", { lineHeight: "1.7", letterSpacing: "0", fontWeight: "400" }],
        "body": ["1rem", { lineHeight: "1.7", letterSpacing: "0", fontWeight: "400" }],
        "body-sm": ["0.875rem", { lineHeight: "1.6", letterSpacing: "0", fontWeight: "400" }],
        "caption": ["0.75rem", { lineHeight: "1.5", letterSpacing: "0.02em", fontWeight: "400" }],
        "code": ["0.875rem", { lineHeight: "1.6", letterSpacing: "0", fontWeight: "400" }],
      },
      transitionDuration: {
        fast: "150ms",
        normal: "200ms",
        slow: "250ms",
      },
      transitionTimingFunction: {
        "ease-out-expo": "cubic-bezier(0.19, 1, 0.22, 1)",
        "ease-in-expo": "cubic-bezier(0.95, 0.05, 0.795, 0.035)",
      },
      boxShadow: {
        "card": "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
        "card-hover": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
        "elevated": "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
        "focus": "0 0 0 3px #DD614C",
      },
    },
  },
  plugins: [],
};

export default config;