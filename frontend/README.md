# Beauty CRM Frontend

Sprint 1 foundation for the enterprise UI.

## Local setup

```bash
npm install
npm run dev
```

Set the backend base URL as needed:

```bash
export NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Structure

- `app/` routes (login + dashboard shell)
- `components/layout/` shared layout primitives
- `lib/api.ts` API client with tenant + auth headers
- `middleware.ts` route protection for dashboard routes
