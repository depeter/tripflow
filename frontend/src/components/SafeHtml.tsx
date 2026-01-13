'use client';

import DOMPurify from 'dompurify';

interface SafeHtmlProps {
  html: string | null | undefined;
  className?: string;
  as?: keyof JSX.IntrinsicElements;
}

/**
 * SafeHtml Component
 *
 * Safely renders HTML content by sanitizing it with DOMPurify.
 * Allows common formatting tags while preventing XSS attacks.
 */
export default function SafeHtml({ html, className = '', as: Component = 'div' }: SafeHtmlProps) {
  if (!html) {
    return null;
  }

  // Configure DOMPurify - allow common formatting tags
  const sanitizedHtml = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'a', 'ul', 'ol', 'li',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div', 'blockquote'
    ],
    ALLOWED_ATTR: ['href', 'target', 'rel', 'class'],
    ALLOW_DATA_ATTR: false,
  });

  // Ensure all links open in new tab with security attributes
  const processedHtml = sanitizedHtml.replace(
    /<a /g,
    '<a target="_blank" rel="noopener noreferrer" '
  );

  return (
    <Component
      className={className}
      dangerouslySetInnerHTML={{ __html: processedHtml }}
    />
  );
}
