---
name: prototype-design-system
description: Use when creating or reviewing HTML prototypes. Defines visual language, tokens, components, responsive behavior, and accessibility baseline. Authoritative values live in templates/design-tokens.json.
---

# Prototype Design System

## Purpose

Provide a unified, reusable, reviewable visual and interaction specification for HTML prototypes.

Authoritative colors, fonts, spacing, and corner-radius values live in `templates/design-tokens.json`.

## Required References

Before generating or modifying a prototype, the following MUST be read:

- `templates/design-tokens.json`
- `templates/prototype-design-system.md` (when the project has confirmed it exists)
- `templates/Prototype.html` (structure and interaction baseline)

The path is decoupled from versioning — the design system is a **template-level constant** and does not belong to any version.

## Prototype Tool Routing

Before generating or modifying `iteration/v{major}.{minor}/01-product/v{major}.{minor}-prototype.html`, the current Agent environment's prototype-preview capability MUST be determined:

1. **Codex environment**: use the `visualize` plugin to create interactive previews or inspect prototype interactions, then produce the final in-project HTML prototype. `visualize` previews support exploration and validation; they do not replace the in-project formal prototype artifact.
2. **Codex without `visualize` installed**: pause prototype generation, tell the user that the plugin is missing, and guide them to install or enable `visualize` in the current Codex environment; do not fall back to no-preview generation until the user confirms.
3. **Other Agent environments**: search the current environment for a plugin or tool that is equivalent to `visualize`; at minimum it must support interactive interface preview, state-switch inspection, or prototype visualization. Record the substitute name and purpose, then continue; if none can be found, pause and ask the user to provide or install a substitute.

The process record MUST include: the runtime environment, the plugin or substitute tool used, the preview or inspection result, and the blocking reason when no tool is available. Plugins that were not actually invoked MUST NOT be reported as used.

## Design Rules

### Visual Language

- Adopt a clean, bright, enterprise SaaS style by default.
- Page background, content panels, text, borders, and state colors MUST come from design tokens.
- Do not introduce undefined colors, font sizes, corner radii, or shadows in CSS.
- Brand-theme changes are made by editing tokens.

### Typography

- Use the font stack from the tokens.
- Establish a clear hierarchy of headings, body, and supporting text.
- Important information MUST NOT rely on color alone.
- Define truncation, wrapping, or expansion behavior for long text.

### Layout

- Use a unified spacing unit.
- Keep the responsibilities of the content area, sidebar, top navigation, and action area distinct.
- Support both desktop and narrow-screen display.

### Components

Prefer reuse:

- Button: primary / secondary / danger / disabled / loading
- Input: default / focus / error / disabled
- Card: title / content / action area
- Table / List: empty / loading / no-result
- Badge / Status: semantic status colors
- Modal / Drawer: confirm / cancel / submit / close
- Toast / Alert: success / warning / error / info

### Interaction States

Every interactive page MUST consider at least:

- initial display
- loading
- empty data
- search no-result
- form-validation failure
- action success feedback
- action failure feedback
- dangerous action confirmation

## CSS Contract

1. Declare the design-token-mapped CSS Custom Properties under `:root`.
2. Component styles must prefer `var(--token-name)` references.
3. Avoid large-scale inline styles.
4. Organize by group: page structure / component styles / interaction states.
5. Keep HTML, CSS, and JS readable so humans can adjust them.

## Accessibility Baseline

- Interactive elements must use semantic HTML.
- Form controls must have visible or programmatically-associated labels.
- Keyboard focus must be visible.
- Color contrast must satisfy ordinary readability requirements.
- Icon-only buttons must provide `aria-label` or visible text.
- Color must not be the only carrier of success / failure / status.

## Review Checklist

- [ ] The page uses the unified theme tokens.
- [ ] No undefined ad-hoc colors or fonts appear.
- [ ] Heading, body, and supporting-text hierarchy is clear.
- [ ] Button / Input / Card / Table components share a consistent style.
- [ ] Empty / loading / error / success states are all covered.
- [ ] Key actions remain understandable on desktop and narrow screens.
- [ ] Keyboard focus, form labels, and icon fallback text are present.

## Notes

- This skill is a template-level specification and is **not bound to any specific version**.
- `templates/prototype-design-system.md` and `templates/design-tokens.json` are two expressions of the same specification; if a project provides its own design system, the decision MUST be recorded in a baseline ADR.
