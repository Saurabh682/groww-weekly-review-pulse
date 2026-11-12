/**
 * Strips Markdown formatting syntax and counts words accurately.
 * Treats ₹5,000, 4.5★, UPI/NEFT, and e-mail as 1 word each.
 */
export function countWords(markdownText: string): number {
  if (!markdownText || typeof markdownText !== 'string') {
    return 0;
  }

  // 1. Remove markdown links, keep text: [text](url) -> text
  let text = markdownText.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');

  // 2. Remove code blocks and inline code markers
  text = text.replace(/```[\s\S]*?```/g, '');
  text = text.replace(/`([^`]+)`/g, '$1');

  // 3. Remove markdown headers, list markers, blockquotes, horizontal rules
  text = text.replace(/^#{1,6}\s+/gm, '');
  text = text.replace(/^[\*\-+]\s+/gm, '');
  text = text.replace(/^\d+\.\s+/gm, '');
  text = text.replace(/^>\s+/gm, '');
  text = text.replace(/^---+$/gm, '');

  // 4. Remove bold/italic markers (*, **, _, __)
  text = text.replace(/(\*\*|__)(.*?)\1/g, '$2');
  text = text.replace(/(\*|_)(.*?)\1/g, '$2');

  // 5. Replace multiple whitespace/newlines with single space
  text = text.replace(/\s+/g, ' ').trim();

  if (text.length === 0) {
    return 0;
  }

  // Split by whitespace
  const tokens = text.split(/\s+/).filter(token => token.length > 0);
  return tokens.length;
}
