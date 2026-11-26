const token = (name) => `color-mix(in srgb, var(--color-${name}) calc(<alpha-value> * 100%), transparent)`;

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: token('bg'),
        'canvas-subtle': token('canvas-subtle'),
        sidebar: token('sidebar'),
        surface: token('surface'),
        'surface-dim': token('surface-dim'),
        'surface-low': token('surface-low'),
        'surface-elevated': token('surface-elevated'),
        'surface-highest': token('surface-highest'),
        border: token('border'),
        'border-subtle': token('border-subtle'),
        'border-glass': token('border-glass'),
        'text-primary': token('text-primary'),
        'text-secondary': token('text-secondary'),
        'text-muted': token('text-muted'),
        'on-surface-variant': token('on-surface-variant'),
        primary: {
          DEFAULT: token('primary'),
          hover: token('primary-hover'),
          tint: token('primary-tint'),
          border: token('primary-border'),
          glow: token('primary-glow'),
          on: token('on-primary'),
        },
        friction: {
          DEFAULT: token('friction'),
          tint: token('friction-tint'),
          border: token('friction-border'),
          glow: token('friction-glow'),
          dark: token('friction-dark'),
        },
        critical: {
          DEFAULT: token('critical'),
          tint: token('critical-tint'),
          border: token('critical-border'),
          glow: token('critical-glow'),
          dark: token('critical-dark'),
        },
        blue: {
          DEFAULT: token('blue'),
          tint: token('blue-tint'),
          border: token('blue-border'),
        },
        failure: {
          DEFAULT: token('failure'),
          tint: token('failure-tint'),
          border: token('failure-border'),
          dark: token('failure-dark'),
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Space Grotesk', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      fontSize: {
        '2xs': '11px',
        '3xs': '10px',
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
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
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
        'fade-in': 'fadeIn 200ms ease-out',
        'pulse-glow': 'pulseGlow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'heartbeat': 'heartbeat 1.6s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
