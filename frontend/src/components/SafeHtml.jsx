import React from 'react';
import DOMPurify from 'dompurify';

/**
 * SafeHtml Component
 *
 * Safely renders HTML content by sanitizing it with DOMPurify.
 * Allows common formatting tags while preventing XSS attacks.
 *
 * @param {string} html - The HTML string to sanitize and render
 * @param {string} className - Optional CSS class name
 * @param {object} config - Optional DOMPurify configuration
 */
const SafeHtml = ({ html, className = '', config = {} }) => {
  if (!html) {
    return null;
  }

  // Default DOMPurify configuration
  const defaultConfig = {
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'a', 'ul', 'ol', 'li',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div', 'blockquote'
    ],
    ALLOWED_ATTR: ['href', 'target', 'rel', 'class'],
    ALLOW_DATA_ATTR: false,
    // Ensure links open in new tab and are safe
    ADD_ATTR: ['target'],
    ...config
  };

  // Sanitize the HTML
  const sanitizedHtml = DOMPurify.sanitize(html, defaultConfig);

  // Additional processing: ensure external links have rel="noopener noreferrer"
  const processedHtml = sanitizedHtml.replace(
    /<a /g,
    '<a target="_blank" rel="noopener noreferrer" '
  );

  return (
    <div
      className={className}
      dangerouslySetInnerHTML={{ __html: processedHtml }}
    />
  );
};

export default SafeHtml;
