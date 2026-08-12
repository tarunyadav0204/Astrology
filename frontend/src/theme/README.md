# AstroRoshni theme contract

## Rules for migrated pages

1. Use semantic tokens from `tokens.css`; do not introduce page-specific hex, RGB, gradient, shadow, radius, spacing, or font values.
2. Use the components exported by `components/Theme` for page shells, containers, buttons, cards, headings, fields, tabs, and dialogs.
3. Choose a page mode intentionally:
   - `editorial` for marketing, learning, and reference pages.
   - `guided` for life-analysis and report experiences.
   - `workspace` or `compact` for chart and calculation tools.
4. Keep astrological meaning in the dedicated planet and status tokens. Brand colors must not encode chart meaning.
5. Every new theme must define every semantic color and chart token and pass contrast checks in all component states.
6. Portal content must use `ThemeModal` or semantic tokens so it follows the `data-theme` value on the document root.
7. Route migrations remain independently reversible until the shared system is proven across all three page modes.

## Changing themes

Use `useTheme()`:

```jsx
const { theme, themes, setTheme } = useTheme();
```

The provider validates theme IDs, persists the choice under `astroroshni_theme`, synchronizes changes across tabs, updates `data-theme` on `<html>`, and updates the browser theme color.

`heritage` is the default for new users. A user's saved selection continues to take precedence after they choose another theme.

## Page migration checklist

- Replace hardcoded colors and gradients with semantic tokens.
- Replace inline presentation styles with component classes or theme primitives.
- Use the shared page shell, header, active-native context, and account controls.
- Cover loading, empty, error, disabled, hover, focus, and selected states.
- Verify keyboard order, visible focus, reduced motion, 200% zoom, and narrow mobile layout.
- Check all registered themes before enabling the route migration flag.
