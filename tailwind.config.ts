import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#edfff2",
          100: "#d6ffe3",
          200: "#acffcb",
          300: "#74f8a7",
          400: "#38de7e",
          500: "#18c767",
          600: "#0f9f52",
          700: "#107c44",
          800: "#106238",
          900: "#0f512f"
        }
      },
      boxShadow: {
        glow: "0 0 60px rgba(24, 199, 103, 0.25)",
        panel: "0 15px 40px rgba(4, 8, 6, 0.45)"
      }
    }
  },
  plugins: []
};

export default config;
