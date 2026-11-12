/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: 'var(--color-bg)',
        'canvas-subtle': 'var(--color-canvas-subtle)',
        sidebar: 'var(--color-sidebar)',
        surface: 'var(--color-surface)',
        'surface-dim': 'var(--color-surface-dim)',
        'surface-low': 'var(--color-surface-low)',
        'surface-elevated': 'var(--color-surface-elevated)',
        'surface-highest': 'var(--color-surface-highest)',
        border: 'var(--color-border)',
        'border-subtle': 'var(--color-border-subtle)',
        'border-glass': 'var(--color-border-glass)',
        'text-primary': 'var(--color-text-primary)',
        'text-secondary': 'var(--color-text-secondary)',
        'text-muted': 'var(--color-text-muted)',
        'on-surface-variant': 'var(--color-on-surface-variant)',
        primary: {
          DEFAULT: 'var(--color-primary)',
          hover: 'var(--color-primary-hover)',
          tint: 'var(--color-primary-tint)',
          border: 'var(--color-primary-border)',
          glow: 'var(--color-primary-glow)',
          on: 'var(--color-on-primary)',
        },
        friction: {
          DEFAULT: 'var(--color-friction)',
          tint: 'var(--color-friction-tint)',
          border: 'var(--color-friction-border)',
          glow: 'var(--color-friction-glow)',
          dark: 'var(--color-friction-dark)',
        },
        critical: {
          DEFAULT: 'var(--color-critical)',
          tint: 'var(--color-critical-tint)',
          border: 'var(--color-critical-border)',
          glow: 'var(--color-critical-glow)',
          dark: 'var(--color-critical-dark)',
        },
        blue: {
          DEFAULT: 'var(--color-blue)',
          tint: 'var(--color-blue-tint)',
          border: 'var(--color-blue-border)',
        },
        failure: {
          DEFAULT: 'var(--color-failure)',
          tint: 'var(--color-failure-tint)',
          border: 'var(--color-failure-border)',
          dark: 'var(--color-failure-dark)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Space Grotesk', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      borderRadius: {
        card: '10px',
        chip: '9999px',
      },
      boxShadow: {
        subtle: '0 1px 3px rgba(0, 0, 0, 0.4)',
        card: '0 8px 32px -4px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05)',
        hover: '0 12px 36px -4px rgba(0, 208, 156, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.08)',
        drawer: '-8px 0 32px rgba(0, 0, 0, 0.7)',
        'glow-teal': '0 0 20px rgba(0, 208, 156, 0.35)',
        'glow-teal-sm': '0 0 10px rgba(0, 208, 156, 0.25)',
        'glow-amber': '0 0 16px rgba(245, 158, 11, 0.3)',
        'glow-coral': '0 0 16px rgba(244, 63, 94, 0.3)',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.9' },
          '50%': { transform: 'scale(1.35)', opacity: '0.35' },
        },
        heartbeat: {
          '0%, 100%': { transform: 'scale(1)' },
          '14%': { transform: 'scale(1.15)' },
          '28%': { transform: 'scale(1)' },
          '42%': { transform: 'scale(1.1)' },
          '70%': { transform: 'scale(1)' },
        },
      },
      animation: {
        'pulse-glow': 'pulseGlow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'heartbeat': 'heartbeat 1.6s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
