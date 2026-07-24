import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Premium Medical Blue - Primary brand color
        medical: {
          50: "#F8FAFC",
          100: "#EEF4F8",
          200: "#D7E4EC",
          300: "#AFC6D6",
          400: "#7697AC",
          500: "#486D86",
          600: "#2C536D",
          700: "#173B57",
          800: "#102A43",
          900: "#0B1F33"
        },
        // Teal Accent - Used for interactive elements, highlights, and CTAs
        teal: {
          50: "#F0FDFA",
          100: "#CCFBF1",
          200: "#99F6E4",
          300: "#5EEAD4",
          400: "#2DD4BF",
          500: "#14B8A6",
          600: "#0F766E",
          700: "#0B635C",
          800: "#0A574B",
          900: "#084C3E"
        },
        // Slate Gray - Secondary colors, text, borders
        slate: {
          50: "#F8FAFC",
          100: "#F1F5F9",
          200: "#E2E8F0",
          300: "#CBD5E1",
          400: "#94A3B8",
          500: "#64748B",
          600: "#475569",
          700: "#334155",
          800: "#1E293B",
          900: "#0F172A"
        },
        // Status colors - Professional, non-saturated
        emerald: {
          50: "#F0FDF4",
          100: "#DCFCE7",
          600: "#16A34A"
        },
        amber: {
          50: "#FFFBEB",
          100: "#FEF3C7",
          600: "#D97706"
        },
        rose: {
          50: "#FFF5F5",
          100: "#FFE7E7",
          600: "#E11D48"
        },
        sky: {
          50: "#F0F9FF",
          100: "#E0F2FE",
          600: "#0284C7"
        }
      },
      boxShadow: {
        // Premium shadows for depth and elevation
        xs: "0 1px 2px 0 rgba(15, 23, 42, 0.05)",
        sm: "0 1px 3px 0 rgba(15, 23, 42, 0.1), 0 1px 2px 0 rgba(15, 23, 42, 0.06)",
        base: "0 4px 6px -1px rgba(15, 23, 42, 0.1), 0 2px 4px -1px rgba(15, 23, 42, 0.06)",
        md: "0 10px 15px -3px rgba(15, 23, 42, 0.1), 0 4px 6px -2px rgba(15, 23, 42, 0.05)",
        lg: "0 20px 25px -5px rgba(15, 23, 42, 0.1), 0 10px 10px -5px rgba(15, 23, 42, 0.04)",
        xl: "0 25px 50px -12px rgba(15, 23, 42, 0.25)",
        // Medical-specific shadows
        med: "0 20px 45px rgba(15, 23, 42, 0.08)",
        panel: "0 10px 30px rgba(15, 23, 42, 0.06)",
        card: "0 4px 12px rgba(15, 23, 42, 0.08)",
        elevated: "0 8px 24px rgba(15, 23, 42, 0.12)"
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["SFMono-Regular", "Consolas", "Liberation Mono", "monospace"]
      },
      fontSize: {
        // Premium typography scale
        xs: ["12px", { lineHeight: "16px", letterSpacing: "0.3px" }],
        sm: ["13px", { lineHeight: "20px", letterSpacing: "0.1px" }],
        base: ["14px", { lineHeight: "21px", letterSpacing: "0.2px" }],
        lg: ["16px", { lineHeight: "24px", letterSpacing: "0.2px" }],
        xl: ["18px", { lineHeight: "28px", letterSpacing: "0" }],
        "2xl": ["20px", { lineHeight: "30px", letterSpacing: "0" }],
        "3xl": ["24px", { lineHeight: "32px", letterSpacing: "0" }],
        "4xl": ["28px", { lineHeight: "36px", letterSpacing: "-0.5px" }],
        "5xl": ["32px", { lineHeight: "40px", letterSpacing: "-0.5px" }]
      },
      borderRadius: {
        sm: "6px",
        base: "8px",
        md: "10px",
        lg: "12px",
        xl: "14px",
        "2xl": "16px"
      },
      spacing: {
        // Enhanced spacing scale for airy layout
        xs: "4px",
        sm: "8px",
        md: "12px",
        lg: "16px",
        xl: "24px",
        "2xl": "32px",
        "3xl": "48px",
        "4xl": "64px"
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fadeIn": "fadeIn 0.3s ease-out",
        "slideUp": "slideUp 0.3s ease-out",
        "slideDown": "slideDown 0.2s ease-out"
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" }
        },
        slideUp: {
          "0%": { transform: "translateY(12px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" }
        },
        slideDown: {
          "0%": { transform: "translateY(-8px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" }
        }
      },
      transitionDuration: {
        fast: "150ms",
        base: "200ms",
        slow: "300ms"
      }
    }
  },
  plugins: []
};

export default config;
