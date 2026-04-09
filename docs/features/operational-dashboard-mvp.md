# Operational Dashboard MVP

## Goal
Provide a fast, operational snapshot for micro-business owners:

- What do I have today?
- What is pending?
- Who should I contact?
- What can I do now with one click?

This is intentionally **operational**, not BI/analytics.

## Scope (MVP)
- Top cards with counts:
  - Appointments today
  - Appointments pending confirmation
  - Tasks today (**empty state**)
  - Inactive customers (no completed appointment in the last **60 days**)
  - Scheduled reminders (**empty state**)
  - Recent no-shows (last **14 days**)
  - New online bookings today (**proxy-based**)
- Short lists (up to 5 items each) for the main sections.
- Quick actions linking to existing dashboard pages.
- Tenant timezone is the source of truth for “today”.

## Backend

### Endpoint
- `GET /crm/dashboard/overview`

### Response shape
- `timezone` + `today_start_utc` + `today_end_utc`
- `counts` (card numbers)
- `sections` (short lists)
- `notes` (documented limitations / empty states)

### Calculations (explicit)
- **Timezone for “today”**: uses tenant settings `default_timezone` (fallback to `UTC` if invalid/missing).
- **Appointments today**:
  - `starts_at` within `[today_start_utc, today_end_utc)`
  - excludes statuses: `completed`, `cancelled`, `no_show`
- **Appointments pending confirmation**:
  - `appointments.needs_confirmation = true`
  - `starts_at >= now`
  - excludes statuses: `completed`, `cancelled`, `no_show`
- **Inactive customers**:
  - customers with **no completed appointment** in the last `60` days
  - includes customers that never completed an appointment
- **Recent no-shows**:
  - appointments with `status = no_show`
  - `status_updated_at >= now - 14 days`
- **New online bookings today (proxy)**:
  - appointments where `created_by_user_id IS NULL`
  - `created_at` within tenant “today” window

### Known limitations
- **Tasks** and **scheduled reminders** do not exist as first-class features yet, so the dashboard returns `0` and empty lists (honest empty state).
- **New online bookings today** is a proxy and may include non-booking-created appointments if the system creates appointments without `created_by_user_id` for other reasons.

## Frontend
- Dashboard home is now the operational overview at:
  - `/dashboard`
- A placeholder route exists for the “Import customers” quick action:
  - `/dashboard/customers/import`

## Next steps (post-MVP)
- Introduce a real appointment `source/origin` field for online bookings (remove proxy).
- Implement Tasks + Reminders as real entities, then backfill dashboard sections.
- Make the inactivity rule configurable per tenant (optional).
- Add filtering by location (optional).

