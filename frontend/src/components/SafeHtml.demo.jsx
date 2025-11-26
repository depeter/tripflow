import React from 'react';
import SafeHtml from './SafeHtml';
import './SafeHtml.demo.css';

/**
 * Demo component to showcase SafeHtml functionality
 * This demonstrates how various HTML content is sanitized and rendered
 */
const SafeHtmlDemo = () => {
  const examples = [
    {
      title: 'Plain Text',
      html: 'This is plain text without any HTML tags.',
      description: 'Basic text content'
    },
    {
      title: 'Formatted Text',
      html: '<p>This is a paragraph with <strong>bold</strong>, <em>italic</em>, and <u>underlined</u> text.</p>',
      description: 'Safe formatting tags'
    },
    {
      title: 'Links',
      html: '<p>Check out this <a href="https://example.com">example link</a> (opens in new tab with security attributes).</p>',
      description: 'External links are made safe with target="_blank" and rel="noopener noreferrer"'
    },
    {
      title: 'Lists',
      html: `
        <p>Things to bring:</p>
        <ul>
          <li>Tent</li>
          <li>Sleeping bag</li>
          <li>Cooking equipment</li>
        </ul>
      `,
      description: 'Unordered and ordered lists'
    },
    {
      title: 'Line Breaks',
      html: 'Line one<br>Line two<br/>Line three',
      description: 'Line breaks are preserved'
    },
    {
      title: 'Dangerous Script Tags (Sanitized)',
      html: '<p>Safe content</p><script>alert("This should be removed")</script>',
      description: 'Script tags are completely removed'
    },
    {
      title: 'Event Handlers (Sanitized)',
      html: '<p onclick="alert(\'XSS\')">Click me (onclick removed)</p>',
      description: 'Event handlers are stripped for security'
    },
    {
      title: 'Typical Event Description',
      html: `
        <h3>Summer Music Festival</h3>
        <p>Join us for an amazing weekend of music, food, and fun!</p>
        <p><strong>Date:</strong> June 15-17, 2025<br>
        <strong>Location:</strong> Central Park</p>
        <p>Featured artists include:</p>
        <ul>
          <li>The Rockers</li>
          <li>Jazz Ensemble</li>
          <li>Electronic Beats DJ</li>
        </ul>
        <p>For more information, visit <a href="https://example.com/festival">our website</a>.</p>
      `,
      description: 'Typical event description with headings, paragraphs, lists, and links'
    },
    {
      title: 'HTML Entities',
      html: '<p>Special characters: &amp; &lt; &gt; &quot; &#39; &copy; &euro;</p>',
      description: 'HTML entities are properly decoded'
    }
  ];

  return (
    <div className="safehtml-demo">
      <h1>SafeHtml Component Demo</h1>
      <p className="demo-intro">
        This page demonstrates how the SafeHtml component handles various types of HTML content,
        including safe formatting and dangerous scripts that get sanitized.
      </p>

      <div className="demo-grid">
        {examples.map((example, index) => (
          <div key={index} className="demo-item">
            <h2>{example.title}</h2>
            <p className="demo-description">{example.description}</p>

            <div className="demo-section">
              <h3>Input (Raw HTML):</h3>
              <pre className="demo-code">{example.html}</pre>
            </div>

            <div className="demo-section">
              <h3>Output (Rendered):</h3>
              <div className="demo-output">
                <SafeHtml html={example.html} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SafeHtmlDemo;
