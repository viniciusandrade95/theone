# TheOne Premium Design System v0.1 — Mist Blue

This directory introduces the first reusable visual foundation for TheOne's premium product experience.

This PR is intentionally foundational only. It does **not** redesign existing product pages.

## Product context

TheOne is evolving into a mobile-first CRM / operating system for service microbusinesses such as:

- barbers
- personal trainers
- nails
- hair professionals
- massage therapists
- beauty and wellness studios

The visual direction is **Mist Blue**: premium-clean, soft, calm, SaaS/wellness, readable, light/dark ready, and less generic-admin-dashboard.

## Design principles

1. **Phone-first** — daily use happens between services and appointments.
2. **Agenda-first** — the user needs to know what happens now, what is next, when there is a pause, and when the day ends.
3. **Action-first** — pending bookings, messages, confirmations and follow-ups should be easy to act on.
4. **Premium-clean** — soft surfaces, clear hierarchy, subtle depth, generous spacing.
5. **Human/direct copy** — prefer “2 bookings para validar” over vague dashboard language.
6. **Maxton as construction kit** — Maxton can provide raw admin/template building blocks, but it is not the product identity.

## Files

```text
frontend/design-system/
  tokens.css
  theme-light.css
  theme-dark.css
  components.css
  README.md
```

## Import order

Use this order when enabling the system in a page or shell:

```css
@import "./tokens.css";
@import "./theme-light.css";
@import "./theme-dark.css";
@import "./components.css";
```

In framework-specific bundling, keep the same order.

## Theme strategy

Light mode is the default.

```html
<html data-theme="light">
```

Dark mode is enabled with:

```html
<html data-theme="dark">
```

The dark theme is not a simple inversion. It has its own surfaces, shadows, borders and soft glass backgrounds.

## Core token groups

### Colors

- `--mb-bg`, `--mb-bg-soft`, `--mb-bg-warm`
- `--mb-surface`, `--mb-surface-soft`, `--mb-surface-glass`
- `--mb-text`, `--mb-muted`, `--mb-muted-2`, `--mb-line`
- `--mb-primary`, `--mb-primary-dark`, `--mb-primary-soft`
- `--mb-accent`, `--mb-accent-soft`
- `--mb-aqua`, `--mb-aqua-soft`
- semantic colors: success, warning, danger

### Layout and feel

- spacing scale: `--mb-space-*`
- radius scale: `--mb-radius-*`
- shadows: `--mb-shadow-*`
- motion: `--mb-motion-*`, `--mb-ease-standard`
- z-index: `--mb-z-*`

## Component primitives

The classes in `components.css` are framework-light primitives intended to be gradually adopted.

### Shells

- `.ds-premium-bg`
- `.ds-responsive-container`
- `.ds-mobile-shell`
- `.ds-tablet-shell`
- `.ds-desktop-shell`

### Cards

- `.ds-card`
- `.ds-card-solid`
- `.ds-card-soft`

### Buttons

- `.ds-button`
- `.ds-button-primary`
- `.ds-button-secondary`
- `.ds-button-ghost`

### Inputs

- `.ds-search`
- `.ds-input`

### Status / labels

- `.ds-chip`
- `.ds-chip-accent`
- `.ds-chip-success`
- `.ds-chip-warning`

### Dashboard primitives

- `.ds-metric-card`
- `.ds-metric-label`
- `.ds-metric-value`
- `.ds-metric-trend`
- `.ds-attention-strip`
- `.ds-attention-title`
- `.ds-attention-subtitle`

### Navigation

- `.ds-mobile-nav`
- `.ds-mobile-nav-item`

## Migration strategy

Do not migrate the whole app at once.

Recommended order:

1. Create the new Home using these primitives.
2. Extract product-specific components such as AgendaStateCard, AttentionStrip, MetricCard, QuickActionsGrid.
3. Apply to Agenda.
4. Apply to Customers.
5. Apply to Services.
6. Apply to New Booking.
7. Revisit Login and Onboarding.

## Responsive product logic

The same components should adapt by device role:

- **Phone:** act now.
- **Tablet:** plan the day.
- **Desktop:** operate the business.

Avoid creating separate products for phone/tablet/desktop. Prefer shared components with different shells and grid behavior.

## Maxton relationship

Maxton is a construction kit:

- layout inspiration
- icons
- admin widgets
- charts/calendar/forms as raw materials

TheOne Premium Design System is the product identity:

- Mist Blue palette
- fine-line/lightweight visual language
- agenda-first hierarchy
- action-first UX
- premium spacing and surface rules
- light/dark theme behavior

## Acceptance notes for this PR

This foundation should not change existing screens until future PRs import and use it. Existing dashboard behavior should remain unchanged.
