# Home v1 — Information Architecture

This document describes the **dashboard home** structure for v1. The goal is 5-second scanability on mobile, with progressively richer context on larger screens.

## Primary intent
- Answer “What needs my attention today?” without navigating.
- Provide a short list of the next actions that create revenue or reduce risk.
- Keep state handling honest when data is MVP/placeholder.

## Sections (mobile-first)

### 1) Context header
- Title: `Overview`
- Subtext: “Today’s operational snapshot. Times shown in {timezone}.”
- Action: Refresh

### 2) Today snapshot (counts)
Compact KPI grid:
- Appointments today
- Pending confirmation
- Inactive customers
- Recent no-shows (14d)
- New online bookings (proxy)
- Tasks / reminders (explicitly “not available yet”)

### 3) Opportunities / next actions
Small cards that translate metrics into action:
- Confirm bookings → link to appointments
- Win back customers → link to customers
- No-show watch → link to appointments
- Online bookings → link to appointments

### 4) Communication delivery (WhatsApp)
Show a conservative delivery breakdown for recent outbound history:
- Sending (queued)
- Sent (accepted/sent by provider)
- Delivered
- Read
- Manual (unconfirmed / deeplink sends)
- Failed

Notes:
- Provider-backed sends are trackable (status updates via webhook callbacks).
- Manual sends can’t be confirmed and should be labeled as such.

### 5) Quick actions
Links to existing product areas (no new functionality implied).

### 6) Operational lists
Short, actionable lists:
- Appointments today
- Appointments pending confirmation
- Inactive customers
- New online bookings (proxy)
- Recent no-shows
- Tasks & reminders (honest empty state)

