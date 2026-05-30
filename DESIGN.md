# Web Crawler Design Foundation

This document extracts the reusable design rules from the provided visual token
contract and adapts them to this Web Crawler CMS. It is intentionally small:
feature-specific UI decisions should reference these rules instead of adding new
raw colors, spacing, or typography choices directly in components.

## Principles

- Use semantic tokens for color, spacing, radius, and motion.
- Keep operational screens dense, calm, and easy to scan.
- Prefer surface color, border, and spacing for hierarchy. Use shadows only when
  an interaction explicitly needs lift, such as article-card hover feedback.
- Keep feature PRs narrow. Update this document first when a new visual rule is
  needed.

## Typography

Primary font stack:

```css
"Zen Kaku Gothic New", "Hiragino Sans", "Yu Gothic", system-ui, sans-serif
```

Weights:

- Display headings: 300
- Body text: 400
- UI emphasis, labels, buttons: 600

Avoid introducing 500 or 700 unless a later design decision updates this file.

## Color Tokens

Use CSS custom properties with the `--crawler-*` prefix.

| Token | Light value | Purpose |
| --- | --- | --- |
| `--crawler-surface-bg` | `#ffffff` | Page background |
| `--crawler-surface-raised` | `#f4f4f4` | Cards and panels |
| `--crawler-surface-muted` | `#e0e0e0` | Selected or secondary areas |
| `--crawler-border-subtle` | `#e0e0e0` | Default borders and dividers |
| `--crawler-border-strong` | `#8d8d8d` | Focus and selected borders |
| `--crawler-text-primary` | `#161616` | Headings and body |
| `--crawler-text-secondary` | `#525252` | Supporting text |
| `--crawler-text-tertiary` | `#6f6f6f` | Metadata and captions |
| `--crawler-accent-primary` | `#0f62fe` | Primary interactive color |
| `--crawler-accent-hover` | `#0353e9` | Primary hover color |
| `--crawler-focus-ring` | `#0f62fe` | Keyboard focus outline |
| `--crawler-text-on-accent` | `#ffffff` | Text on accent backgrounds |

## Spacing

Use an 8px base grid.

| Token | Value |
| --- | --- |
| `--crawler-space-1` | `8px` |
| `--crawler-space-2` | `16px` |
| `--crawler-space-3` | `24px` |
| `--crawler-space-4` | `32px` |
| `--crawler-space-5` | `40px` |
| `--crawler-space-6` | `48px` |
| `--crawler-space-8` | `64px` |

Avoid new 4px, 12px, 20px, or other off-grid spacing in feature work.

## Radius

| Token | Value | Purpose |
| --- | --- | --- |
| `--crawler-radius-sm` | `8px` | Small controls and chips |
| `--crawler-radius-md` | `11px` | Inputs and secondary controls |
| `--crawler-radius-lg` | `18px` | Article cards and panels |
| `--crawler-radius-pill` | `9999px` | Search fields and primary pills |

## Motion

| Token | Value | Purpose |
| --- | --- | --- |
| `--crawler-duration-fast` | `150ms` | Hover and press feedback |
| `--crawler-duration-base` | `200ms` | Standard UI transitions |
| `--crawler-duration-slow` | `300ms` | Panel transitions |
| `--crawler-easing-out` | `cubic-bezier(0.22, 1, 0.36, 1)` | Default easing |

Respect `prefers-reduced-motion` by disabling or shortening transitions.

## Component Guidance

- Article lists should prioritize fast scanning: title, excerpt, image, and a
  compact row of metadata.
- Form controls should use pill or medium radius, visible focus outlines, and
  high contrast labels.
- Bulk-selection states should use `--crawler-surface-muted` rather than pure
  white, plus a strong border or accent marker for selected items.
- Comments are content, not metadata. Keep them visually quieter than article
  titles but more readable than timestamps.
