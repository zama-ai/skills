# Migration from Older Frontend Patterns

## Recognition Heuristics

Look for signs such as:

- direct relayer bootstrap in UI components
- decrypt or sign flows triggered on render
- custom balance refresh loops outside React Query patterns
- ad hoc storage handling for credentials

## Migration Order

1. Move SDK bootstrap into `ZamaProvider`.
2. Replace manual flows with official hooks.
3. Replace implicit signing with explicit `useAllow` UX.
4. Move persistence to the documented storage utilities.
5. Rebuild invalidation and refresh behavior with `tanstack-best-practices`.

## Old to New Mapping

- relayer setup in UI components -> `ZamaProvider`
- decrypt-on-render flow -> `useIsAllowed()` + user-triggered `useAllow()`
- custom unwrap resume state -> `loadPendingUnshield()` + `useResumeUnshield()`
- custom polling loops -> React SDK hooks + TanStack Query patterns
- custom storage glue -> `indexedDBStorage` and session storage from the approved examples

## Do Not

- keep decrypt-on-render behavior
- rebuild provider state from scratch before reading the approved examples
- preserve outdated frontend patterns just because they still compile
