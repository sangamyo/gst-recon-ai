/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#2F6FED",
        secondary: "#0F172A",
      },
    },
  },
  plugins: [],
};
