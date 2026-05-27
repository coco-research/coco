/**
 * InboxPage — thin re-export wrapper.
 *
 * The phase-6 v3 redesign moved the implementation to `./inbox/InboxPage.tsx`
 * (3-zone deck: Briefing · Decision Deck · Resolved Log). This file is the
 * route entry point referenced by `App.tsx`. Keeping it as a re-export lets
 * the router stay stable while the implementation evolves in `./inbox/`.
 */

export { default } from './inbox/InboxPage';
