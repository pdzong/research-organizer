# Tailwind CSS Dependency Fix

## Issue
The frontend failed to start with error:
```
Cannot find module 'tailwindcss'
```

## Cause
The project uses Tailwind CSS (configured in `postcss.config.cjs` and used in `index.css`), but the dependencies were missing from `package.json`.

## Solution Applied
Added missing dependencies to `devDependencies`:
- `tailwindcss` ^3.4.1
- `autoprefixer` ^10.4.16

## Verification
Run the frontend:
```bash
cd web_ui
npm run dev
```

Should now start successfully without PostCSS errors! ✅

## Note
The project uses both **Mantine** (component library) and **Tailwind CSS** (utility classes) together, which is why both are present.
