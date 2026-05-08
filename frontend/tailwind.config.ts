import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'aether-blue': '#00A8E8',
        'aether-cyan': '#00C9FF',
        'dark-bg': '#0f172a',
      },
    },
  },
  plugins: [],
}
export default config
