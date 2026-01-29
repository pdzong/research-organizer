/** @type {import('tailwindcss').Config} */
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}"
  ],
  darkMode: 'class', // Enable dark mode with class strategy
  theme: {
    extend: {
      colors: {
        // Linear-inspired dark palette
        'linear-dark': {
          'bg': '#0D0D0D',
          'surface': '#1A1A1A',
          'border': '#2A2A2A',
          'hover': '#252525',
          'text': '#E0E0E0',
          'muted': '#888888',
        },
      },
      borderRadius: {
        'linear': '8px',
      },
      boxShadow: {
        'linear': '0 0 0 1px rgba(255, 255, 255, 0.1)',
        'linear-hover': '0 0 0 1px rgba(255, 255, 255, 0.2)',
        'linear-focus': '0 0 0 2px rgba(255, 255, 255, 0.3)',
      },
    },
  },
  plugins: [],
};

export default config;
