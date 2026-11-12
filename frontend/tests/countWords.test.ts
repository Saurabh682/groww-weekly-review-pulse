import { describe, it, expect } from 'vitest';
import { countWords } from '../src/lib/countWords';

describe('countWords', () => {
  it('correctly counts plain words', () => {
    expect(countWords('Groww Weekly Review Pulse')).toBe(4);
    expect(countWords('Hello world')).toBe(2);
    expect(countWords('')).toBe(0);
    expect(countWords('   ')).toBe(0);
  });

  it('strips markdown headers, lists, and bold/italic', () => {
    const md = `
# Executive Summary
**Groww App** performance for the week.
* Bullet point item one
* Bullet point item two
> A blockquote text here
    `.trim();

    // "Executive Summary Groww App performance for the week Bullet point item one Bullet point item two A blockquote text here"
    // Executive(1) Summary(2) Groww(3) App(4) performance(5) for(6) the(7) week.(8)
    // Bullet(9) point(10) item(11) one(12) Bullet(13) point(14) item(15) two(16)
    // A(17) blockquote(18) text(19) here(20)
    expect(countWords(md)).toBe(20);
  });

  it('strips markdown links keeping link text only', () => {
    const md = 'Check the [Google Doc Link](https://docs.google.com/123) for details.';
    expect(countWords(md)).toBe(7); // "Check the Google Doc Link for details."
  });

  it('treats currency amounts, ratings, compound terms as single words', () => {
    const text = 'User transferred ₹5,000 with 4.5★ rating via UPI/NEFT through e-mail verification.';
    // User(1) transferred(2) ₹5,000(3) with(4) 4.5★(5) rating(6) via(7) UPI/NEFT(8) through(9) e-mail(10) verification.(11)
    expect(countWords(text)).toBe(11);
  });
});
