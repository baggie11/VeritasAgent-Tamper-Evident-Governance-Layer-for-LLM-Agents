/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./app/components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#f3efe8",
        card: "#fffdf8",
        ink: "#1f2b34",
        accent: "#0b6e4f",
        danger: "#a4161a"
      }
    }
  },
  plugins: []
};
