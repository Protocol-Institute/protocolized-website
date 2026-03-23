/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#0F6E56",
          light: "#E1F5EE",
        },
        secondary: "#5F5E5A",
        surface: "#F9F8F5",
        accent: "#D85A30",
        dark: "#2C2C2A",
      },
      fontFamily: {
        serif: ["Instrument Serif", "Georgia", "serif"],
        body: ["Lora", "Georgia", "serif"],
        sans: ["Outfit", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Courier New", "monospace"],
      },
      maxWidth: {
        prose: "768px",
        wide: "1200px",
      },
      typography: (theme) => ({
        DEFAULT: {
          css: {
            color: theme("colors.dark"),
            fontFamily: theme("fontFamily.body").join(", "),
            "h1, h2, h3, h4": {
              fontFamily: theme("fontFamily.serif").join(", "),
              color: theme("colors.dark"),
            },
            a: {
              color: theme("colors.primary.DEFAULT"),
              "&:hover": { color: "#085041" },
            },
          },
        },
      }),
    },
  },
  plugins: [],
};
