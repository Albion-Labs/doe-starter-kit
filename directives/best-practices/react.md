# Best Practices: React

## Goal
Prevent common agent failure modes in React before they reach commit.

## When to Use
Read before writing or modifying any React component or hook.

## Process

### Correctness
- Always include a complete dependency array in `useEffect` — missing deps cause stale closures, empty array when truly mount-only
- Never mutate state directly — always use the setter from `useState` or return new objects/arrays
- Always provide a stable, unique `key` prop in lists — never use array index as key for lists that reorder, filter, or grow
- Never use `useEffect` to compute derived state — calculate it during render instead (simpler, fewer re-renders)
- Always return a cleanup function from `useEffect` when it creates subscriptions, timers, or event listeners
- Never call hooks conditionally or inside loops — hooks must always be at the top level of the component

### Performance
- Never define functions inline in JSX props when the child component uses `React.memo` — extract to `useCallback` or define outside render
- Never create new objects/arrays in JSX props — extract to `useMemo` or define outside render
- Split components over 200 lines — large components are hard to test, reuse, and debug

### Architecture
- Never prop-drill through 3+ levels — use Context, composition (`children`), or state management
- Keep side effects in `useEffect` or event handlers — never in the render body
- Never mix data fetching with presentation — separate container/data components from display components
- Always handle loading, error, and empty states — never assume data is present on first render

### Maintainability
- Never leave `console.log` in committed components
- Always name components with PascalCase and use named exports for easier debugging
- Never use `dangerouslySetInnerHTML` without explicit sanitisation

## Verification
- [ ] All `useEffect` calls have correct dependency arrays
- [ ] No direct state mutation
- [ ] All lists have stable, unique `key` props
- [ ] No `useEffect` for derived state
- [ ] Side effects have cleanup functions where needed
- [ ] No components over 200 lines without justification
