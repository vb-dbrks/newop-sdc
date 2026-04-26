import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        velocia: {
          DEFAULT: "#a51d70",
          hover: "#7d1f50",
          light: "#fce4ec",
        },
        badge: {
          newop: "#fbbf24",
          sdc: "#3b82f6",
        },
        ink: "#0a0a0a",
        muted: "#64748b",
        line: "#e2e8f0",
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        slab: ['"Roboto Slab"', "Inter", "serif"],
      },
      borderRadius: {
        velocia: "10px",
      },
      boxShadow: {
        pill: "0 8px 24px -8px rgba(165, 29, 112, 0.45)",
      },
    },
  },
  plugins: [],
} satisfies Config;
