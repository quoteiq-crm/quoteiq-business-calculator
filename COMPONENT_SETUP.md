# The Infinite Grid — component integration

## Important: this repo is not (yet) a React/shadcn project

`index.html` is a single, self-contained static page. It has **no** `package.json`,
TypeScript, Tailwind build, or React. So the `.tsx` component cannot run here as-is.

You have two paths:

- **Path A — see it now (already done):** the Infinite Grid effect (infinitely
  scrolling grid + cursor-follow reveal + soft color blobs) has been ported to
  **vanilla HTML/CSS/JS** inside `index.html`, used as the hero/header background.
  No dependencies, still one copy/paste file.
- **Path B — use the real React component:** stand up a shadcn + Tailwind +
  TypeScript app and drop the files in. Instructions below.

The component files have been added exactly as provided:

```
components/ui/the-infinite-grid.tsx   # the component (exports `Component`)
components/ui/demo.tsx                 # usage example (exports default DemoOne)
lib/utils.ts                           # cn() helper the component imports
```

## Why components live in `/components/ui`

shadcn/ui's convention (set in `components.json` via the `aliases` field) is that
primitives live in `@/components/ui`. Keeping this folder matters because:

1. The import in `demo.tsx` is `@/components/ui/the-infinite-grid` — the `@/*`
   alias must resolve to your source root (configured in `tsconfig.json`
   `paths` and your bundler), and `components/ui` is where the CLI expects and
   writes primitives.
2. `npx shadcn@latest add <name>` installs into `components/ui`. Matching that
   path keeps CLI-added and hand-added components consistent and avoids broken
   imports.

## Path B — full setup from scratch

```bash
# 1. New Vite + React + TypeScript app (or use Next.js)
npm create vite@latest my-app -- --template react-ts
cd my-app
npm install

# 2. Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# 3. shadcn/ui (creates components.json, sets up @/ alias, base tokens)
npx shadcn@latest init      # choose your style + base colour, components dir = components/ui

# 4. This component's dependencies
npm install framer-motion           # animation engine the component uses
npm install clsx tailwind-merge     # used by lib/utils.ts cn()
```

Then copy `components/ui/the-infinite-grid.tsx`, `components/ui/demo.tsx`, and
`lib/utils.ts` from this repo into the new app, ensure `@/*` resolves to your
`src` (in `tsconfig.json` `compilerOptions.paths`: `"@/*": ["./src/*"]` and the
matching Vite `resolve.alias`), and render `<DemoOne />`.

The component relies on these shadcn theme tokens (created by `shadcn init`):
`bg-background`, `text-foreground`, `text-muted-foreground`, `bg-primary`,
`text-primary-foreground`, `bg-secondary`, `text-secondary-foreground`. Without
`shadcn init` these classes won't exist and the component will render unstyled.

## Integration questions — answered

- **What data/props will be passed in?** None. `Component` takes no props; it
  owns its own `count` state and mouse/grid motion values internally. (If you
  want it configurable, lift `speedX/speedY`, grid size, and the heading/body
  copy into props.)
- **State management requirements?** Local only — `useState` for the click
  counter and Framer Motion `useMotionValue`/`useAnimationFrame` for cursor
  position and the scrolling grid offset. No context/store needed.
- **Required assets?** None. The visuals are pure SVG + CSS gradients/blurs;
  no images or fonts. (If you add icons later, use `lucide-react`.)
- **Expected responsive behaviour?** Full-viewport (`w-full h-screen`),
  content centered; the headline scales `text-4xl → md:text-6xl`. The grid and
  blobs are percentage/viewport based, so it adapts to any size.
- **Best place to use it?** As a hero/landing background or a section backdrop.
  In this project it's been wired in as the **header background** of
  `index.html`.

## What the vanilla port maps to

| React component piece            | Vanilla equivalent in `index.html`                 |
|----------------------------------|----------------------------------------------------|
| scrolling `GridPattern` (0.05)   | `.grid-base` (CSS `gridscroll` keyframes)          |
| cursor-revealed grid (opacity 40)| `.grid-reveal` (radial `mask-image` at `--mx/--my`)|
| orange / primary / blue blobs    | `.blob-warm` / `.blob-rust` / `.blob-cool` (brand) |
| `handleMouseMove`                | hero `mousemove` → sets `--mx`/`--my`              |

Colours were mapped to the Steep brand palette (apricot / rust / sky) instead of
the generic orange/blue so the grid stays on-brand.
