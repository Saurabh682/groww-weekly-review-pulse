import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import postcss from 'postcss';
import tailwindcss from 'tailwindcss';
import { describe, expect, it } from 'vitest';
import config from '../tailwind.config.js';

const SRC = path.resolve(__dirname, '../src');
const PALETTE =
  'slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose';

function files(): { file: string; text: string }[] {
  return readdirSync(SRC, { recursive: true, encoding: 'utf-8' })
    .filter((file) => file.endsWith('.tsx') || file.endsWith('.ts'))
    .map((file) => ({ file, text: readFileSync(path.join(SRC, file), 'utf-8') }));
}

function offenders(pattern: RegExp): string[] {
  return files().flatMap(({ file, text }) => (text.match(pattern) ?? []).map((hit) => `${file}: ${hit}`));
}

function pageFiles(): { file: string; text: string }[] {
  return files().filter(({ file }) => !file.split(path.sep).join('/').startsWith('components/'));
}

function classLists(text: string): string[] {
  return [...text.matchAll(/className=(?:"([^"]*)"|\{`([^`]*)`\})/g)].map((m) => m[1] ?? m[2]);
}

function pageClassOffenders(test: (classes: string) => boolean): string[] {
  return pageFiles().flatMap(({ file, text }) =>
    classLists(text)
      .filter(test)
      .map((classes) => `${file}: ${classes}`),
  );
}

describe('pages take colours and sizes from the theme', () => {
  it('test_UIC_01_no_hex_colour_classes', () => {
    expect(
      offenders(/-\[#[0-9a-fA-F]{3,8}\]/g),
      'A hex colour class is banned. Use the theme colour of the same value from tailwind.config.js (surface, border, sidebar, primary-on and so on).',
    ).toEqual([]);
  });

  it('test_UIC_02_no_pixel_text_sizes', () => {
    expect(
      offenders(/text-\[\d+px\]/g),
      'A pixel text size is banned. Use text-2xs (11px) or text-3xs (10px) from the theme, or the Badge or Chip component.',
    ).toEqual([]);
  });

  it('test_UIC_03_no_default_palette_colours', () => {
    expect(
      offenders(new RegExp(`(?<![\\w-])(?:bg|border|text|fill|stroke|ring|from|to|via)-(?:${PALETTE})-\\d{2,3}\\b`, 'g')),
      'A Tailwind palette colour is banned. Use a theme colour: primary, friction-dark, critical-dark, blue, text-secondary and so on.',
    ).toEqual([]);
  });

  it('test_UIC_04_every_animation_exists', async () => {
    const raw = files().map(({ text }) => text).join('\n');
    const used = [...new Set(raw.match(/(?<![\w-])animate-[a-z-]+/g))].sort();
    expect(used).toContain('animate-fade-in');
    const { css } = await postcss([tailwindcss({ ...config, content: [{ raw, extension: 'tsx' }] })]).process(
      '@tailwind utilities;',
      { from: undefined },
    );
    expect(
      used.filter((name) => !css.includes(`.${name}`)),
      'An animation class with no rule does nothing. Add it to the theme in tailwind.config.js or remove it.',
    ).toEqual([]);
  });

  it('test_UIC_09_no_colour_literals', () => {
    expect(
      offenders(/#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b(?!\{)|rgba?\(/g),
      'A hex or rgba colour is banned in code. Use CSS_COLOUR from styles/cssColours.ts in SVG attributes and styles, or a theme class.',
    ).toEqual([]);
  });

  it('test_UIC_10_cards_take_only_layout_classes', () => {
    const passed = files().flatMap(({ file, text }) =>
      [...text.matchAll(/<Card\b(?:(?!<)[\s\S])*?className=(?:"([^"]*)"|\{`([^`]*)`\})/g)].map(
        (m) => `${file}: ${m[1] ?? m[2]}`,
      ),
    );
    expect(passed.length).toBeGreaterThan(10);
    expect(
      passed.filter((hit) => /(?:^|[\s:"])!?(?:[a-z]+:)*(?:p[xytblr]?-|bg-|border|shadow-|rounded)/.test(hit.split(': ')[1])),
      'Card takes only layout classes. Use its padding, variant and tone props for padding, colour and border.',
    ).toEqual([]);
  });

  it('test_UIC_11_pages_use_the_shared_button', () => {
    expect(
      pageFiles()
        .filter(({ text }) => text.includes('<button'))
        .map(({ file }) => file),
      'A raw <button> is banned in pages. Use Button, or a shared component from components/.',
    ).toEqual([]);
  });

  it('test_UIC_12_pages_use_the_shared_pill_and_card', () => {
    expect(
      pageClassOffenders((c) => /rounded-full/.test(c) && /\bpx-/.test(c) && /-tint\b|bg-surface\b/.test(c)),
      'A hand-written pill is banned in pages. Use Chip or Badge.',
    ).toEqual([]);
    expect(
      pageClassOffenders((c) => /rounded-(?:xl|card)\b/.test(c) && /\bbg-surface\b/.test(c) && /(?:^|\s)border(?:\s|$)/.test(c)),
      'A hand-written card box is banned in pages. Use Card.',
    ).toEqual([]);
  });
});
