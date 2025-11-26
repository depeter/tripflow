import React from 'react';
import { render, screen } from '@testing-library/react';
import SafeHtml from './SafeHtml';

describe('SafeHtml Component', () => {
  test('renders plain text without HTML', () => {
    const { container } = render(<SafeHtml html="Simple text" />);
    expect(container.textContent).toBe('Simple text');
  });

  test('renders safe HTML tags', () => {
    const html = '<p>This is a <strong>bold</strong> paragraph</p>';
    const { container } = render(<SafeHtml html={html} />);
    expect(container.querySelector('p')).toBeInTheDocument();
    expect(container.querySelector('strong')).toBeInTheDocument();
    expect(container.textContent).toContain('This is a bold paragraph');
  });

  test('renders links with proper attributes', () => {
    const html = '<a href="https://example.com">Click here</a>';
    const { container } = render(<SafeHtml html={html} />);
    const link = container.querySelector('a');
    expect(link).toBeInTheDocument();
    expect(link.getAttribute('href')).toBe('https://example.com');
    expect(link.getAttribute('target')).toBe('_blank');
    expect(link.getAttribute('rel')).toBe('noopener noreferrer');
  });

  test('sanitizes dangerous HTML', () => {
    const html = '<p>Safe content</p><script>alert("XSS")</script>';
    const { container } = render(<SafeHtml html={html} />);
    expect(container.querySelector('script')).not.toBeInTheDocument();
    expect(container.textContent).toBe('Safe content');
  });

  test('removes event handlers', () => {
    const html = '<p onclick="alert(\'XSS\')">Click me</p>';
    const { container } = render(<SafeHtml html={html} />);
    const paragraph = container.querySelector('p');
    expect(paragraph).toBeInTheDocument();
    expect(paragraph.getAttribute('onclick')).toBeNull();
  });

  test('handles br tags and line breaks', () => {
    const html = 'Line 1<br>Line 2<br/>Line 3';
    const { container } = render(<SafeHtml html={html} />);
    const breaks = container.querySelectorAll('br');
    expect(breaks.length).toBe(2);
  });

  test('returns null for empty HTML', () => {
    const { container } = render(<SafeHtml html="" />);
    expect(container.firstChild).toBeNull();
  });

  test('returns null for null HTML', () => {
    const { container } = render(<SafeHtml html={null} />);
    expect(container.firstChild).toBeNull();
  });

  test('applies custom className', () => {
    const html = '<p>Test</p>';
    const { container } = render(<SafeHtml html={html} className="custom-class" />);
    expect(container.firstChild).toHaveClass('custom-class');
  });

  test('handles nested HTML structures', () => {
    const html = `
      <div>
        <h2>Title</h2>
        <p>Paragraph with <em>emphasis</em> and <strong>strong</strong> text.</p>
        <ul>
          <li>Item 1</li>
          <li>Item 2</li>
        </ul>
      </div>
    `;
    const { container } = render(<SafeHtml html={html} />);
    expect(container.querySelector('h2')).toBeInTheDocument();
    expect(container.querySelector('em')).toBeInTheDocument();
    expect(container.querySelector('ul')).toBeInTheDocument();
    expect(container.querySelectorAll('li').length).toBe(2);
  });
});
