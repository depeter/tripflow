# SafeHtml Component

## Overview

The `SafeHtml` component safely renders HTML content by sanitizing it with DOMPurify. It prevents XSS (Cross-Site Scripting) attacks while allowing safe formatting tags.

## Features

- ✅ **XSS Protection**: Removes dangerous scripts and event handlers
- ✅ **Formatting Preserved**: Keeps safe HTML like `<p>`, `<strong>`, `<em>`, `<br>`
- ✅ **Link Safety**: Automatically adds `target="_blank"` and `rel="noopener noreferrer"` to links
- ✅ **Configurable**: Customize which tags are allowed
- ✅ **Lightweight**: Uses industry-standard DOMPurify library

## Installation

DOMPurify is already installed as a dependency:

```bash
npm list dompurify
# dompurify@3.3.0
```

## Usage

### Basic Usage

```jsx
import SafeHtml from './components/SafeHtml';

function MyComponent() {
  const htmlContent = '<p>This is <strong>bold</strong> text.</p>';

  return <SafeHtml html={htmlContent} />;
}
```

### With CSS Class

```jsx
<SafeHtml
  html={event.description}
  className="event-description"
/>
```

### Custom Configuration

```jsx
<SafeHtml
  html={content}
  config={{
    ALLOWED_TAGS: ['p', 'br', 'strong'],
    ALLOWED_ATTR: ['class']
  }}
/>
```

## Allowed Tags (Default)

By default, the following HTML tags are allowed:

- **Text formatting**: `<p>`, `<br>`, `<strong>`, `<b>`, `<em>`, `<i>`, `<u>`, `<span>`
- **Headings**: `<h1>`, `<h2>`, `<h3>`, `<h4>`, `<h5>`, `<h6>`
- **Lists**: `<ul>`, `<ol>`, `<li>`
- **Containers**: `<div>`, `<blockquote>`
- **Links**: `<a>` (with href, target, rel, class attributes)

## Blocked Content

The following are **automatically removed**:

- `<script>` tags
- `<iframe>` tags
- Event handlers (onclick, onerror, etc.)
- Data attributes
- Dangerous URLs (javascript:, data:, etc.)

## Examples

### Before Sanitization

```html
<p>Event info</p>
<script>alert('XSS')</script>
<p onclick="danger()">Click me</p>
```

### After Sanitization

```html
<p>Event info</p>
<p>Click me</p>
```

### Safe HTML Preserved

```html
Input:
<h3>Festival</h3>
<p>Join us for <strong>music</strong> and <em>fun</em>!</p>
<ul>
  <li>Food trucks</li>
  <li>Live music</li>
</ul>
<p>More info at <a href="https://example.com">our site</a></p>

Output: (all tags preserved and rendered safely)
```

## Where It's Used

The SafeHtml component is currently used in:

1. **EventCard.jsx** - Event descriptions in discovery cards
2. **LocationCard.jsx** - Location descriptions
3. **Step6_ReviewFinalize.jsx** - Trip itinerary descriptions

## Testing

Run the test suite:

```bash
npm test SafeHtml.test.jsx
```

View the demo page (add to your router):

```jsx
import SafeHtmlDemo from './components/SafeHtml.demo';

// In your routes:
<Route path="/demo/safehtml" element={<SafeHtmlDemo />} />
```

## Security Notes

- Always use `SafeHtml` for user-generated content or external data
- Never use `dangerouslySetInnerHTML` directly without sanitization
- Links automatically open in new tabs with security attributes
- Regular DOMPurify updates ensure protection against new threats

## API Reference

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `html` | string | - | The HTML string to sanitize and render |
| `className` | string | `''` | CSS class name for the wrapper div |
| `config` | object | `{}` | DOMPurify configuration object |

### DOMPurify Config Options

See [DOMPurify documentation](https://github.com/cure53/DOMPurify#can-i-configure-dompurify) for all options.

Common options:
- `ALLOWED_TAGS`: Array of allowed tag names
- `ALLOWED_ATTR`: Array of allowed attribute names
- `FORBID_TAGS`: Array of forbidden tag names
- `FORBID_ATTR`: Array of forbidden attribute names

## Troubleshooting

**Issue**: HTML is not rendering, showing as plain text
- Check that you're passing the HTML as a string prop, not children
- Verify DOMPurify is installed: `npm list dompurify`

**Issue**: Some tags are being removed
- Check if the tag is in the `ALLOWED_TAGS` list
- Pass a custom `config` prop to allow additional tags

**Issue**: Links not opening properly
- Links automatically get `target="_blank"` - this is intentional for security
- External links should open in a new tab

## References

- [DOMPurify GitHub](https://github.com/cure53/DOMPurify)
- [OWASP XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
