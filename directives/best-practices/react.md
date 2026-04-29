# Best Practices: React

## Goal
Prevent common agent failure modes in React before they reach commit.

## When to Use
Read before writing or modifying any React component or hook.

## Process

### Correctness
- Always include a complete dependency array in `useEffect` — missing deps cause stale closures, empty array when truly mount-only
- Apply state changes via the setter from `useState` or by returning new objects/arrays from a reducer -- the mutation/replacement distinction is what triggers React's re-render
- Provide a stable, unique `key` prop in lists -- prefer a record id; array index is only safe when the list is read-only and never reordered
- Compute derived state during render (or in `useMemo` for expensive cases) -- `useEffect` for derivation costs an extra render and risks stale closures
- Always return a cleanup function from `useEffect` when it creates subscriptions, timers, or event listeners
- Call hooks at the top level of the component, in the same order on every render -- React tracks hook state by call order, so conditional or looped hooks break that mapping

### Performance
- For `React.memo`'d children, extract callback props to `useCallback` or define them outside render -- inline arrow functions create a new identity each render, defeating memoisation
- For object/array props passed to memoised children, extract to `useMemo` or define outside render -- a fresh object each render breaks reference equality
- Split components over 200 lines — large components are hard to test, reuse, and debug

### Architecture
- For data needed 3+ levels deep, use Context, component composition (`children`), or external state management -- prop-drilling couples intermediate components to data they don't read
- Side effects belong in `useEffect` or event handlers -- the render body must be pure so React can re-run it without observable consequences
- Separate data-fetching components from display components -- the data layer holds loading/error/state machinery, the display layer renders props
- Always handle loading, error, and empty states — never assume data is present on first render

### Maintainability
- Never leave `console.log` in committed components
- Always name components with PascalCase and use named exports for easier debugging
- When `dangerouslySetInnerHTML` is unavoidable (Markdown render, sanitised CMS payload), pass through DOMPurify or an equivalent allowlist sanitiser first -- the API name is a warning sign for unscoped use

## Verification
- [ ] All `useEffect` calls have correct dependency arrays
- [ ] No direct state mutation
- [ ] All lists have stable, unique `key` props
- [ ] No `useEffect` for derived state
- [ ] Side effects have cleanup functions where needed
- [ ] No components over 200 lines without justification
