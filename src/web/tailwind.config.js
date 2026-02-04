/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx,html}"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Roboto', 'sans-serif'],
        serif: ['Charis SIL', 'serif'],
        mono: ['Roboto Mono', 'monospace']
      },
      colors: {
        // Base Neutrals (High Contrast in both palettes)
        base: {
          dark: '#161616',       // Level 1: Carbon Black (Neutral)
          'dark-dim': '#1C1E26', // Level 2: Cool Black (Blue tint for depth)
          light: '#F4F4F4',      // Level 1: Bone White (Max brightness)
          'light-dim': '#E6E6E6',// Level 2: Muted White (Structural separation)
        },
        // IBM Palette (UI Elements Only)
        ibm: {
          blue: '#648FFF', purple: '#785EF0', pink: '#DC267F',
          orange: '#FE6100', yellow: '#FFB000'
        },
        // Bang Wong Palette (Data Visualization Only)
        wong: {
          orange: '#E69F00', sky: '#56B4E9', green: '#009E73',
          blue: '#0072B2', vermilion: '#D55E00'
        },
        // Legacy mapping for existing components
        'gram-primary': '#56B4E9',
        'gram-secondary': '#009E73',
        'gram-accent': '#E69F00',
      }
    },
  },
  plugins: [],
}