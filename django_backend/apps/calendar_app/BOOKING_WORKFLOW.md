# Consultation booking

This addition covers public consultation requests, the office appointment calendar,
and appointment dashboard metrics. Existing matter events and other modules are unchanged.

## Workflow

1. `/rendez-vous`: choose a consultation type and active practice area.
2. Choose a day from the month calendar and an available hour, then OFFICE, VIDEO or PHONE.
3. Submit contact details, a description (10–5000 characters), and consent.
4. The backend validates office hours and reserves the fixed slot as `PENDING`.
   The receipt contains a reference and the reserved time; no email or video link is sent.
5. Trusted office staff see the same appointment on `/app/calendar` and `/app`.
   The views refresh on focus, after an action, and every 30 seconds while visible.
6. Staff can confirm a future pending request, cancel pending/confirmed requests,
   or complete a confirmed consultation after its end. Cancellation releases the slot.
   Terminal states cannot be reactivated. Dashboard links open the appointment's week.

## Initial schedule

`config/settings.py: BOOKING` sets Sunday–Thursday, 09:00–17:00, 60-minute
consultations, at least 60 minutes' notice, and a 90-day booking horizon.
The office timezone is Africa/Algiers. Frontend display helpers in
`frontend1/src/features/appointments/bookingUtils.ts` use the same timezone.
Capacity is **one consultation per slot across the office**, not per lawyer or specialty.
The Friday/Saturday closure and these hours are initial assumptions, not a supplied office policy.
Do not change the slot grid/duration while existing reservations overlap the new grid
without migrating those reservations; uniqueness is enforced by fixed slot start.

An initial “Consultation générale” area is seeded by migration. Manage actual areas
and active flags in Django Admin. Appointments are read-only in Admin; use the calendar
for status changes so transition rules remain enforced.

## Access

Public endpoints return practice areas, schedule configuration, free slots, and a
booking receipt only. They never list clients or other visitors' contact details.
Booking creation is limited to 20 requests/hour/IP using Django's default cache.
Use a shared cache and correctly configured proxy handling for a multi-worker deployment.

Private endpoints require a Django superuser, or `is_staff=True` plus role
`SUPER_ADMIN`/`INTERNAL_ASSOCIATE`. An authorized administrator must grant staff access.
The legacy registration endpoint accepts role input; trusting role alone would expose
booking details. This implementation does not change account registration or grant staff
rights to existing accounts. Client/partner users cannot list or manage office bookings.

## API

All routes below are under `/api/v1/`:

| Method and route | Purpose |
|---|---|
| GET `public/practice-areas/` | Active consultation areas |
| GET `public/booking-config/` | Date bounds, weekdays, duration, timezone |
| GET `appointments/availability/?date=YYYY-MM-DD&specialty=slug` | Available fixed slots |
| POST `public/bookings/` | Persist a public booking; 201 or 409 if reserved concurrently |
| GET `appointments/?from=YYYY-MM-DD&to=YYYY-MM-DD` | Staff calendar, up to 366-day range |
| POST `appointments/{id}/confirm/` | Pending → confirmed |
| POST `appointments/{id}/cancel/` | Pending/confirmed → cancelled |
| POST `appointments/{id}/complete/` | Finished confirmed → completed |
| GET `dashboard/` | Today's appointments, next ten, pending/upcoming/confirmed counts |

POST booking fields: `practice_area`, `start_at` (ISO timestamp with offset),
`consultation_type`, `full_name`, `email`, `phone`, `legal_topic`, `description`,
optional `opposing_party`, and `consent=true`. The server calculates `end_at` and status.
A conditional database uniqueness constraint prevents concurrent reservations of a slot.
On conflict the public form reloads free slots and preserves contact details.

## Validation

```powershell
.\.venv\Scripts\python.exe manage.py test apps.calendar_app
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

18 tests cover validation, closed/past/off-grid dates, notice, timezone equivalence,
permissions, privacy, dashboard/calendar consistency, transitions, cancellation,
throttling, database uniqueness and simultaneous booking requests.

`frontend1/scripts/booking-smoke.mjs` exercises the real mobile booking UI, concurrent
slot conflict recovery, contact retention, receipt, login, dashboard, staff calendar,
confirmation and cancellation. Run only against an isolated database with a trusted
staff fixture. Supply `SMOKE_FRONTEND_URL`, `SMOKE_API_URL`, `SMOKE_CDP_URL`,
`SMOKE_USERNAME`, and `SMOKE_PASSWORD`. It uses Node 22+ and a headless Chrome CDP
endpoint, with no added npm dependency. Screenshots go to the OS temporary directory.
