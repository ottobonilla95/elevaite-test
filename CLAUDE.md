# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Lint/Test Commands
- Build: `npm run build` or `turbo build`
- Dev: `npm run dev` or `turbo dev`
- Lint: `npm run lint` or `turbo lint`
- Type check: `npm run type-check` or `turbo type-check`
- Format: `npm run format`
- Single test (Python): `pytest path/to/test_file.py::test_function_name`

## Code Style
- TypeScript: Use strict type checking with proper interfaces
- Next.js apps follow standard file-based routing
- React components use functional style with hooks
- CSS: Use Tailwind with SCSS modules for components
- Python: PEP8 style with type hints
- Imports: Group by external/internal/relative paths
- Error handling: Use proper try/catch and error boundaries
- Naming: camelCase for JS/TS, snake_case for Python
- Monorepo structure with shared packages in `/packages`