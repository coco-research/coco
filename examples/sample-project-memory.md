# Project Memory — Weather Dashboard

## Overview
- Purpose: Real-time weather dashboard with city search, forecasts, and saved locations
- Stack: React 18, Vite, Vitest, Tailwind CSS, OpenWeather API
- Started: 2026-02-15

## Architecture
- Entry: src/main.jsx
- Structure:
  - src/pages/ — Dashboard, Settings, CityDetail
  - src/components/ — SearchBar, WeatherCard, ForecastChart, LocationList
  - src/services/ — weatherApi.js, localStorage.js
  - src/hooks/ — useWeather.js, useGeolocation.js, useLocalStorage.js

## Key Decisions
- [2026-02-15] Chose Vite over CRA — faster builds, native ESM, smaller bundle
- [2026-02-15] Using localStorage for saved cities — no backend needed for MVP
- [2026-02-16] OpenWeather free tier (60 calls/min) — sufficient for personal use
- [2026-02-16] Tailwind CSS over styled-components — utility-first, smaller CSS output
- [2026-02-17] Added error boundary around API calls — graceful offline handling

## Recent Changes
- [2026-02-15 10:30] `package.json` — Initialized project with Vite + React template
- [2026-02-15 11:00] `src/services/weatherApi.js` — Created OpenWeather API client with env-var key
- [2026-02-15 14:00] `src/components/SearchBar.jsx` — Added city autocomplete with debounced fetch
- [2026-02-16 09:00] `src/pages/Dashboard.jsx` — Built main dashboard with 5-day forecast grid
- [2026-02-16 11:00] `src/hooks/useLocalStorage.js` — Custom hook for persisting saved cities
- [2026-02-16 15:00] `src/components/ForecastChart.jsx` — Added temperature trend visualization
- [2026-02-17 10:00] `src/components/WeatherCard.jsx` — Fixed: was showing stale data after city switch. Root cause: useEffect dependency array missing `cityId`. Added `cityId` to deps.
- [2026-02-17 14:00] `tailwind.config.js` — Added custom weather color palette (clear-sky, cloudy, rain, storm)

## Open Questions
- [2026-02-17] Should we cache API responses? Could reduce API calls by 50-70%
- [2026-02-17] Consider adding push notifications for severe weather alerts?

## Commands
- Dev: npm run dev
- Build: npm run build
- Test: npx vitest run
- Lint: npx eslint src/
