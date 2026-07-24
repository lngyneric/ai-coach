---
title: Learner Experience Redesign (Course Chat Player)
status: proposed
owner_surface: frontend
last_reviewed: 2026-07-21
canonical: true
---

# Learner Experience Redesign (Course Chat Player)

## Summary

Redesign the learner-facing course player (`/c/[[...id]]`) around a unified
token-based design system, a rebuilt chat reading experience, and a phased
migration that keeps legacy `c-*` compatibility surfaces working until each
slice is replaced.

This document is the design baseline. Implementation slices are tracked as
ExecPlans under `docs/exec-plans/active/`.

## Background and Problems

Evidence from the current codebase:

1. **Two parallel styling systems.** The new stack (Tailwind v4 + shadcn/ui
   tokens in `src/app/globals.css`) coexists with a legacy variable set in
   `src/app/c/layout.css` (`--color-1` … `--color-21`, `--font-size-*`) and
   ~40 SCSS/CSS modules (`*.module.scss`). Colors and spacing are not
   derivable from one token source.
   - Evidence: `src/cook-web/src/app/globals.css`,
     `src/cook-web/src/app/c/layout.css`,
     `src/cook-web/tailwind.config.ts`
2. **Duplicated component generations.** `src/c-components/` (legacy) and
   `src/app/c/[[...id]]/Components/` (current) both carry ChatUi, NavDrawer,
   Settings, Pay variants. `PopupModal.tsx` still carries
   `// TODO: Migrate to shadcn/ui`.
3. **A 94 KB god-hook.** Chat behavior, streaming, interaction handling, and
   ask-state live in `ChatUi/useChatLogicHook.tsx`, making visual iteration
   risky because layout and logic are entangled.
   - Evidence:
     `src/cook-web/src/app/c/[[...id]]/Components/ChatUi/useChatLogicHook.tsx`
4. **Layout decided in JS, not CSS.** `calcFrameLayout()`
   (`src/c-constants/uiConstants.ts`) switches between four
   `FRAME_LAYOUT_*` modes via container width + UA sniffing. This blocks
   standard responsive patterns and causes mobile sequencing bugs
   (`docs/product-specs/mobile-404-sequencing-followup.md`).
5. **Dark mode tokens exist but are unwired.** `.dark` variables are defined
   in `globals.css`; `AppContext.theme` is always `''`.
6. **Type-safety debt.** Dozens of `@ts-expect-error EXPECT` in CourseCatalog,
   NavDrawer, and Settings components.
7. **Hardcoded strings risk.** Repo rule: no hardcoded user-facing strings;
   all copy must go through i18n keys served by `/api/i18n`.

## Goals

- One token source: all learner-surface colors, spacing, radii, typography,
  and elevation derive from `globals.css` CSS variables consumed through
  Tailwind v4.
- One component generation: learner surfaces use shadcn/ui primitives in
  `src/components/ui/` plus composed feature components; legacy `c-components`
  shrink to zero over the migration.
- Layout in CSS: responsive behavior expressed with Tailwind breakpoints and
  container queries; JS layout mode reduced to feature flags (e.g. listen
  mode), not geometry.
- Working dark mode: class-based toggling wired to user settings
  (`Components/Settings/UserSettings.tsx`) with `prefers-color-scheme`
  default.
- Visual quality bar: a focused, readable chat canvas with clear message
  hierarchy, an accessible outline (course catalog), and a calm, brandable
  header/footer.

## Non-Goals

- No redesign of `/admin/*`, `/shifu/*`, `/login`, or `/payment` surfaces in
  this plan (they adopt the same tokens later as a follow-up).
- No backend API contract changes. All existing `c-api` calls and business
  codes stay intact (`src/lib/request.ts` remains the only transport).
- No i18n infrastructure changes; only new keys added through the shared
  `src/i18n/` inventory.
- No removal of legacy `c-*` surfaces until the owning ExecPlan retires them
  (per `src/cook-web/AGENTS.md`: treat them as maintained compatibility
  surfaces).

## Current vs Target

### Current layout (desktop)

```
┌───────────────────────────────────────────────┐
│ absolute header 64px (course avatar + name)   │
├──────────┬────────────────────────────────────┤
│ NavDrawer│ chat stream (ContentBlock loop)    │
│ (JS-sized│ AskBlock / InteractionBlock        │
│  width)  ├────────────────────────────────────┤
│          │ absolute footer 40px               │
└──────────┴────────────────────────────────────┘
```

- Geometry from `calcFrameLayout()`; mobile swaps to `ChatMobileHeader` +
  overlay drawer.
- Listen mode replaces the stream with `ListenModeSlideRenderer` +
  `ListenPlayer`.

### Target layout (desktop)

```
┌──────────────────────────────────────────────────────┐
│ TopBar 56px: course identity · mode switch · user    │
├────────────┬─────────────────────────────────────────┤
│ Outline    │ ChatCanvas (max-w 760px, centered)      │
│ (280px,    │  - message blocks, breathing rhythm     │
│  sticky,   │  - inline interactions as cards         │
│  collaps.) │  - AskComposer docked bottom            │
│            ├─────────────────────────────────────────┤
│            │ StatusFooter 32px (disclaimer · power)  │
└────────────┴─────────────────────────────────────────┘
```

- `<768px`: single column; outline becomes a `Sheet` (shadcn) drawer;
  TopBar keeps course title + drawer trigger; composer stays docked.
- `768–1279px`: outline overlays as a collapsible rail (icon strip 56px).
- `≥1280px`: full outline column 280px; chat canvas centered with
  `max-width: 760px` for readable line length.
- Listen mode keeps its own full-bleed variant but shares TopBar tokens.

### Target visual language

- **Tone**: calm, focused "learning companion". Generous whitespace, single
  accent color, no competing chrome.
- **Color**: keep brand primary `#0f63ee` as `--primary`; neutral gray scale
  from existing shadcn tokens; semantic colors only for
  success/warning/destructive states. Dark mode uses the already-defined
  `.dark` palette, audited for contrast (WCAG AA for body text).
- **Typography**: Inter (already shipped via `@fontsource/inter`) + system
  CJK stack. Scale (rem): 12 caption / 14 body-secondary / 16 body / 18
  lead / 20 title / 24 page-title. Chat body at 16px, line-height 1.7.
- **Elevation**: flat surfaces with 1px `--border` separators; dialogs and
  drawers use `shadow-lg` + overlay; no nested cards inside chat messages.
- **Motion**: 150–250 ms ease-out transitions on drawers, mode switches, and
  message entry (fade + 4px rise). Respect `prefers-reduced-motion`.
- **Iconography**: lucide-react only on learner surfaces (Heroicons retired
  there to keep one icon voice).

### Key component redesigns

| Surface | Current | Target |
|---|---|---|
| Chat stream | `NewChatComp.tsx` + `ContentBlock.tsx` mixed logic/view | `ChatCanvas` (view-only) fed by a `useChatController` hook; blocks rendered by a typed `BlockRenderer` registry |
| Message bubble | `ContentBlock` with module SCSS | Token-styled blocks; AI content un-bubbled (full-width markdown), user asks right-aligned with `--accent` bubble |
| Interactions | `InteractionBlock` + `InteractionBlockM` (two variants) | One `InteractionCard` built on shadcn `Card` + `RadioGroup`/`Checkbox`; responsive by container, not by JS variant |
| Ask composer | `AskBlock.tsx` | `AskComposer`: docked textarea with autosize, send/shortcut hints, disabled states driven by ask-state store |
| Outline | `CourseCatalog*` trio with `@ts-expect-error` | Typed `OutlineTree` (section/lesson rows, progress dots, active tracking) in a `Sheet` on mobile |
| Pay wall | `PayModal` + `PayModalM` | One `PayDialog` (shadcn `Dialog`) with responsive width; channel list unchanged (contract with backend) |
| Header/Footer | absolute 64px/40px | Normal-flow `TopBar` 56px / `StatusFooter` 32px; no absolute overlap of the scroll port |

## Architecture Changes

### Design tokens

- Extend `src/app/globals.css` as the single token source:
  - keep shadcn naming (`--background`, `--foreground`, `--primary`,
    `--muted`, `--accent`, `--destructive`, `--border`, `--ring`,
    `--radius`);
  - add learner-specific semantic tokens (`--chat-canvas-bg`,
    `--bubble-user-bg`, `--outline-active-bg`, `--composer-border`) that map
    to base tokens per theme;
  - port the markdown-flow-ui alias block (currently marked `HACK`) into a
    documented `@layer base` mapping so the library's variable expectations
    are satisfied explicitly.
- Deprecate `src/app/c/layout.css`: new components must not consume
  `--color-*`/`--font-size-*` legacy variables; existing consumers are
  migrated per slice and the file is deleted at the end of Phase 3.
- Remove `tailwind.config.ts` token duplication once Tailwind v4 CSS-first
  config covers the theme (keep the file only if the build still requires
  it; document the decision in the slice ExecPlan).

### Component architecture

- Introduce `src/cook-web/src/features/learner/` for new learner components:
  - `features/learner/chat/` — `ChatCanvas`, `BlockRenderer`,
    `useChatController`
  - `features/learner/outline/` — `OutlineTree`, `OutlineRail`
  - `features/learner/composer/` — `AskComposer`
  - `features/learner/pay/` — `PayDialog`
  - `features/learner/shell/` — `LearnerShell` (TopBar + footer + outlet)
- Split `useChatLogicHook.tsx` into:
  - `useChatController` (stream state, block list model)
  - `useAskController` (question send, ask-state store bridge)
  - `useInteractionController` (option submit, interaction results)
  - view components receive plain props; hooks own side effects.
- State: keep Zustand v5 stores (`useCourseStore`, `useSystemStore`,
  `useUiLayoutStore`) but stop using `frameLayout` for geometry in new
  components; `useUiLayoutStore` keeps environment flags (`inWeixin`,
  `inIos`) only.

### Responsive strategy

- Replace geometry decisions with CSS: Tailwind breakpoints
  (`md: 768px`, `xl: 1280px`) and, where component-local, container queries
  via Tailwind v4 support.
- `calcFrameLayout()` remains only for legacy components during migration;
  new shell must not read `FRAME_LAYOUT_*`.
- Mobile drawer uses shadcn `Sheet`; desktop outline uses a sticky aside —
  the same `OutlineTree` component renders in both (no `*M.tsx` fork).

### Dark mode

- Wire `darkMode: 'selector'` to a `theme` field in user settings store:
  `light | dark | system` (default `system` via `prefers-color-scheme`).
- Apply/remove `.dark` on `<html>` in `app/c/layout.tsx` effect; persist
  choice with existing settings API.

### Accessibility

- Keyboard: outline tree roving tabindex; composer `Cmd/Ctrl+Enter` to send;
  dialogs trap focus (Radix default).
- Screen readers: message list as `role="log"` with polite updates; block
  types get `aria-label` from i18n keys.
- Contrast: audit all token pairs against WCAG AA; adjust `.dark` palette
  where failing.

## i18n and Content Rules

- All new copy uses keys from the shared inventory; no hardcoded strings in
  components (`docs/engineering-baseline.md` hard rule).
- New namespaces (if needed) follow the existing `src/i18n/` layout and are
  loaded through the unified backend (`src/lib/unified-i18n-backend.ts`).
- Code-facing text (this doc, component names, ExecPlans) stays in English
  per repository convention.

## Phased Migration Plan

Each phase ships behind a route-level flag so `/c/[[...id]]` can render old
or new shell per course/flag until cutover. Every phase is its own ExecPlan
with acceptance criteria, type-check, lint, focused Jest, and Playwright
smoke (`npm run test:e2e`) before merge.

### Phase 0 — Foundations (no visual change)

- Create `features/learner/` scaffold and `LearnerShell` rendered behind
  `?shell=v2` query flag (or env flag for dev).
- Token audit: map every legacy `--color-*` usage to a target token;
  publish the mapping table in the ExecPlan.
- Add dark-mode toggle plumbing to user settings (hidden until Phase 2).
- Exit: shell renders current components unchanged; zero legacy token usage
  in new files; CI checks green.

### Phase 1 — Chat core rebuild

- Extract `useChatController`/`useAskController`/`useInteractionController`
  from `useChatLogicHook.tsx` (behavior-preserving; covered by focused
  tests).
- Build `ChatCanvas` + `BlockRenderer` with token styling; route old
  `NewChatComp` behind flag.
- Rebuild `AskComposer` and unify `InteractionCard`.
- Exit: desktop chat pixel-parity ± new tokens; mobile via breakpoints;
  old `ContentBlock` still serves flagged-off traffic.

### Phase 2 — Navigation, chrome, and pay

- `OutlineTree` + mobile `Sheet`; `TopBar`/`StatusFooter` replace absolute
  header/footer.
- Unify `PayDialog`; retire `PayModalM` fork.
- Enable dark mode end-to-end; contrast audit fixes.
- Exit: no `FRAME_LAYOUT_*` reads in `features/learner/`; legacy
  `ChatMobileHeader` unreferenced by v2 shell.

### Phase 3 — Legacy retirement and polish

- Migrate remaining `c-components` consumers (PopupModal → shadcn
  `Dialog`); delete `src/app/c/layout.css` and dead `c-components` files in
  the owning ExecPlan only (per AGENTS compatibility rule).
- Remove `@ts-expect-error` debt in touched learner files; add strict types
  for outline tree data (`useLessonTree`).
- Motion polish, `prefers-reduced-motion`, final Playwright visual smoke.
- Exit: `/c/[[...id]]` default-renders v2 shell; flag removed after one
  stable release; architecture-boundary check
  (`scripts/check_architecture_boundaries.py`) updated if file layout
  changed.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Behavior regressions from splitting the god-hook | Phase 1 is behavior-preserving; add hook-level tests before view swap; ship behind flag |
| Mobile/WeChat sequencing bugs resurface | Keep the ordering gates from `mobile-404-sequencing-followup.md`; extend Playwright mobile smoke to `/c/:id` cold open |
| Token migration stalls mid-way | Mapping table + lint rule forbidding legacy `--color-*` in `features/learner/`; layout.css deletion is an explicit Phase 3 gate |
| markdown-flow-ui styling breaks | Documented `@layer base` alias mapping; visual smoke on markdown-heavy lesson |
| Two shells drifting during flag period | Flag is route-level and time-boxed; Phase 3 removes it; no new features land in legacy shell |
| i18n key gaps block UI copy | Keys added in the same PR as components; CI i18n key check (`npm run i18n:keys`) |

## Validation

- `cd src/cook-web && npm run type-check && npm run lint`
- Focused Jest for touched stores/hooks
- `npm run test:e2e` Playwright smoke (desktop + mobile viewport) for
  `/c/:id` open, outline navigation, ask flow, pay dialog open
- Manual: dark mode toggle, WeChat webview spot check, 320px width check

## Open Questions

1. Brand accents: keep `#0f63ee` for the sysmex deployment or introduce a
   per-tenant `--primary` override via runtime config (`useEnvStore` already
   carries branding fields)?
2. Should the video course page `/c/v/[id]` adopt the v2 shell in Phase 2 or
   a later spec?
3. Do we want a storybook-style catalog page for `features/learner/`
   components, or are Playwright smokes + focused Jest enough coverage?

## References

- `src/cook-web/AGENTS.md` — frontend hard rules (transport, i18n, legacy
  c-* compatibility)
- `docs/engineering-baseline.md` — repo engineering handbook
- `docs/product-specs/mobile-404-sequencing-followup.md` — mobile init
  ordering constraints
- `ARCHITECTURE.md` — system surfaces and knowledge model
- `PLANS.md` — ExecPlan specification for the phase slices
