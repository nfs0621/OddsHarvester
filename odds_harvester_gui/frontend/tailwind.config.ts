import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: "class",
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'dark-bg': '#0A0F1A', // Very dark blue
        'dark-card': '#1A202C', // Dark blue for cards
        'dark-primary': '#6366F1', // Indigo 500
        'dark-secondary': '#8B5CF6', // Violet 500
        'dark-accent': '#38BDF8', // Sky 400
        'dark-text-primary': '#E0E0E0', // Light gray text
        'dark-text-secondary': '#A0AEC0', // Lighter gray text
        'dark-border': '#2D3748', // Gray 700 for borders
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
export default config