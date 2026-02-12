import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#f8fafc',
        surface: '#ffffff',
        muted: '#64748b',
        brand: '#111827'
      }
    }
  },
  plugins: []
};

export default config;
