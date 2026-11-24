import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import postcss from 'postcss';
import tailwindcss from 'tailwindcss';
import { expect, it } from 'vitest';
import config from '../tailwind.config.js';

const SRC = path.resolve(__dirname, '../src');
const SEE_THROUGH =
  /(?<![\w-])(?:bg|border|text|stroke|fill)-(?:background|canvas|sidebar|surface|border|text|primary|friction|critical|blue|failure)[a-z-]*\/\d+/g;

function sources(): string {
  return readdirSync(SRC, { recursive: true, encoding: 'utf-8' })
    .filter((file) => file.endsWith('.tsx'))
    .map((file) => readFileSync(path.join(SRC, file), 'utf-8'))
    .join('\n');
}

it('every see-through theme colour the pages use exists in the built CSS', async () => {
  const raw = sources();
  const used = [...new Set(raw.match(SEE_THROUGH))].sort();
  expect(used).toContain('bg-surface/80');
  const { css } = await postcss([tailwindcss({ ...config, content: [{ raw, extension: 'tsx' }] })]).process(
    '@tailwind utilities;',
    { from: undefined },
  );
  const selectors = css.split('\\').join('');
  expect(used.filter((name) => !selectors.includes(name))).toEqual([]);
});
