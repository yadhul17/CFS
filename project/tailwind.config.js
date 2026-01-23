
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // Points to all HTML files inside your Django apps
    "./**/templates/**/*.html", 
    // Points to any JS files in static
    "./**/static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'fund-cyan': '#06b6d4',
      },
      borderRadius: {
        'fund-xl': '3rem',
      }
    },
  },
  plugins: [],
}