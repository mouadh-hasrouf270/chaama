# CHAAMA API and integration guide

## Architecture and compatibility

The existing Django modular monolith, SQLite database, DRF, SimpleJWT and
drf-spectacular remain in use. No dependency versions changed.

- Existing authentication: `POST /api/token/`, `POST /api/token/refresh/`,
  `POST /api/accounts/logout/`, `GET /api/accounts/me/`.
- Existing account/profile routes remain under `/api/accounts/`.
- New business APIs: `/api/v1/`.
- OpenAPI: `/api/schema/`; Swagger UI: `/api/docs/`.
- New lists use page-number pagination: `count`, `next`, `previous`, `results`.
  Default page size 25; `page_size` maximum 100. Availability returns a slot array.
- JWT requests use `Authorization: Bearer <access>`. Login uses the existing
  **username**, not email. No User fields, roles or token behavior were changed.
- PracticeArea and LawyerProfile were extended in place. Client was reused.
  Organization memberships are metadata; they do not confer new global privileges.

## Permission policy

| Resource | Anonymous | Client | Internal associate | External subcontractor | Super admin / Django superuser |
| --- | --- | --- | --- | --- | --- |
| Public practice areas / verified lawyers | Read | Read | Read | Read | Read |
| Public availability and booking submission | Allowed | Allowed | Allowed | Allowed | Allowed |
| Client directory | No | No | Own created clients | Own created clients | All |
| Client deletion | No | No | No | No | Unlinked records only |
| Appointments / intakes / evidence | No | Own linked/created appointments | Assigned or created appointments | Assigned or created appointments | All |
| Calendar blocks / working hours | No | No | Own calendar | Own calendar | All |
| Partner directory | No | No | Read | Read | Read |
| Assistance requests | No | No | No | Create/read own | Read/review all |
| Notifications | No | Own | Own | Own | Own |
| Audit API | No | No | No | No | Read only |

Intake conflict warnings and assistance conflict warnings are admin-only fields.
No matched party names or other clients' records are exposed in those results.
Only the assigned lawyer or admin may review an intake or change appointment
status/meeting URL. A client can reschedule/cancel their own appointment.
Sensitive downloads enforce the same appointment scope before opening the file.

## Endpoints

All paths in this table start with `/api/v1/`.

| Method | Path | Notes |
| --- | --- | --- |
| GET | `public/practice-areas/` | Active records |
| GET | `public/practice-areas/{id}/` | Active record |
| GET | `public/lawyers/` | Active users, lawyer roles, verified profiles |
| GET | `public/lawyers/{id}/` | Public professional fields only |
| GET | `partners/` | External lawyers, scoped by caller role |
| GET | `partners/{id}/` | Profile ID, not User ID |
| GET, POST | `clients/` | Search and paginated directory / offline client creation |
| GET, PUT, PATCH, DELETE | `clients/{id}/` | Existing account client policy |
| GET | `appointments/availability/` | Public query; no private booking/block information |
| GET, POST | `appointments/` | List accessible appointments / create |
| GET, PATCH | `appointments/{id}/` | Scoped read/reschedule/update |
| POST | `appointments/{id}/cancel/` | Idempotent cancellation of already-cancelled appointment |
| GET, POST | `working-hours/` | Recurring weekly working windows |
| GET, PUT, PATCH, DELETE | `working-hours/{id}/` | Own/admin calendar |
| GET, POST | `calendar-blocks/` | Unavailable intervals |
| GET, PUT, PATCH, DELETE | `calendar-blocks/{id}/` | Own/admin calendar |
| POST | `public/bookings/` | Atomic anonymous appointment + intake; minimal receipt |
| GET, POST | `intakes/` | Scoped list / submit for accessible appointment |
| GET | `intakes/{id}/` | Audited access |
| POST | `intakes/{id}/review/` | Assigned lawyer/admin marks reviewed or review required |
| POST | `intakes/{id}/files/` | Multipart evidence upload |
| GET | `intakes/{id}/files/{file_id}/download/` | Authorized attachment download |
| GET, POST | `assistance-requests/` | Admin lists all; external lawyer creates/lists own |
| GET | `assistance-requests/{id}/` | Scoped detail |
| POST | `assistance-requests/{id}/approve/` | Admin human review |
| POST | `assistance-requests/{id}/decline/` | Admin human review |
| GET | `notifications/` | Caller only |
| POST | `notifications/{id}/read/` | Caller only |
| POST | `notifications/read-all/` | Caller only |
| GET | `audit-logs/` | Admin only |
| GET | `audit-logs/{id}/` | Admin only |
| GET | `dashboard/` | Real, scoped aggregates |

Organizations/memberships use Django admin because no management page exists in
React. Existing `/api/accounts/practice-areas/` and lawyer APIs continue to manage
their original resources. The existing project uses hard deletion of practice
areas; deactivation is additionally available through `is_active: false`.

### Filters

- Clients: `search` matches first_name, last_name, email or phone; `city`;
  `ordering=first_name`, `last_name`, `created_at` and their negative forms.
- Public lawyers/partners: `specialty=<practice slug>`, `jurisdiction`,
  `bar_association`, `available=true|false`, `verified=true|false`.
  Public lawyers are always verified even if a caller requests otherwise.
- Appointments: `status`, `lawyer`, `consultation_type`.
- Assistance: `status`, `jurisdiction`.
- Notifications: `is_read=true|false`.
- Audit: `action`, `object_type`, `user`.

## Configure actual booking availability

No fake schedules or demo records were inserted into the project database.

1. Create a lawyer through the existing admin account API or Django admin.
   The existing INTERNAL_ASSOCIATE/EXTERNAL_SUBCONTRACTOR roles create profiles.
2. Create active practice areas and assign them to the lawyer.
3. Admin verifies the profile; set `availability_status=AVAILABLE`.
   Newly extended profiles default to UNAVAILABLE until deliberately configured.
4. Create actual working hours through `POST /api/v1/working-hours/` as the lawyer
   or admin. Weekday: Monday=0, Sunday=6.
5. Set `BOOKING_TIME_ZONE` in the environment if appropriate. It defaults to the
   existing Django TIME_ZONE (UTC). The availability response includes the zone.
6. Add calendar blocks for absences. Existing reservations cannot be blocked over
   silently; cancel/reschedule them explicitly first.

Example working window:

```json
{"lawyer": 1, "weekday": 0, "start_time": "09:00", "end_time": "17:00"}
```

Availability request:

```text
GET /api/v1/appointments/availability/?date=2026-10-05&specialty=criminal-law
```

Use a real slug returned by the practice-area API. Dates must be within 90 days.
Availability is working windows minus active appointments and calendar blocks.
Intervals use half-open bounds: a booking ending at 10:00 permits one starting at
10:00. Default slots are 30 minutes. Bookings require a future, positive interval,
within working hours, with a maximum duration of four hours.

Every calendar write acquires the same lawyer-row lock before reading conflicts.
A first-statement write serializes SQLite writers as well as row-locking on
PostgreSQL. A competing/unavailable booking returns HTTP 409. Direct ORM/bulk/SQL
writes bypass this business service and must not be used to create reservations.

## Public booking example

The existing public form does not choose a named lawyer: it selects the first
available matching lawyer for the chosen specialty/time. Returned slot times are
shown in the configured booking timezone. The server always rechecks availability.

```json
{
  "lawyer": 1,
  "practice_area": 1,
  "start_at": "2026-10-05T09:00:00Z",
  "end_at": "2026-10-05T09:30:00Z",
  "consultation_type": "OFFICE",
  "full_name": "Example Client",
  "email": "client@example.com",
  "phone": "+213555123456",
  "legal_topic": "Initial consultation",
  "description": "A description of the consultation request.",
  "opposing_party": "Example Company",
  "consent": true
}
```

Consultation types: OFFICE, VIDEO, PHONE. Returns HTTP 201:

```json
{"status": "submitted"}
```

The appointment and intake are created in one transaction; no partial booking
survives validation failure. This deliberately anonymous endpoint does not link
an existing client based only on a claimed phone/email and never returns private
client/intake identifiers. Authenticated clients use `POST appointments/` and
`POST intakes/` for account-linked booking. The current public UI uses the
anonymous combined submission. Anonymous submission is throttled to 10/hour/IP.

Appointment statuses: PENDING, CONFIRMED, CANCELLED, COMPLETED.
Closed appointments cannot be rescheduled; clients cannot set professional status.
Confirmation/completion is performed by the assigned lawyer/admin; future
appointments cannot be marked completed.

## Intakes, evidence and conflict warnings

Intake statuses: SUBMITTED, REVIEW_REQUIRED, REVIEWED. One intake per appointment.
The assigned lawyer/admin can POST `{"status":"REVIEWED"}` to the review action.

Files: multipart field `file`; PDF, PNG or JPEG only; 10 MB maximum; extension,
claimed MIME and signature validation. Names use UUID storage keys. Storage lives
under `private_evidence/`, which is git-ignored and is **not** mounted as public
media. Never expose that directory through the deployment web server. File
responses are attachments with no-store/nosniff headers. Storage keys/paths are
absent from serializers. These checks are not malware scanning.

Conflict matching normalizes case, accents and punctuation and searches existing
client full names, intake opposing parties and assistance opposing parties.
Results: NO_MATCH, POSSIBLE_MATCH, REVIEW_REQUIRED (including missing party
information). This is an initial warning, never a legal determination; exact
normalized matching may miss aliases and fuzzy matches. No `CONFLICT_CONFIRMED`
status exists. Extend the source service with MatterParty only in the future.

## Assistance workflow

External lawyers submit their own requests, with optional proposed_fee and
fee_share_percentage (0–100). A possible conflict places the request in
CONFLICT_REVIEW; otherwise PENDING. Only admin can approve/decline.
On approval of a warning, the admin must explicitly submit:

```json
{"acknowledge_conflict": true}
```

Review records reviewed_by/reviewed_at and notifies the requester. Reviewed
requests cannot be reviewed again. Acceptance never creates a Matter in this
phase; the service contains the future integration-point comment.

## Audit, notifications and dashboard

Notifications are transactionally stored for appointment creation/cancellation,
intake submission to the assigned lawyer, assistance submission to admins, and
assistance approval/decline to the requester. They are in-app notifications only.

Audit records include actor, action, model label/object ID, direct request IP,
user-agent and a server-authored metadata allowlist. Passwords, JWTs, submitted
descriptions and file paths are not copied into audit metadata. Client create/
update (including self-update), booking changes, intake reads/review/uploads/
downloads, calendar changes and assistance review are logged. Normal model/API/
admin update and delete are blocked; underlying database administrators still
control the database. Organization is nullable when an action has no direct
organization relation.

Dashboard consistently omits all Matter-dependent fields. It returns:
today_appointments (at most 100), upcoming_appointments (next 10), pending_intakes,
pending_assistance_requests, unread_notifications, clients_count. Visibility is
derived from the caller's existing role and object relationships.

## Frontend and test execution

In `frontend1`, set `VITE_API_BASE_URL` if necessary; default is
`http://127.0.0.1:8000/api`. Use the existing `npm run dev`, `npm run build`,
and `npm run lint`. The shared Axios layer stores JWTs in sessionStorage,
refreshes expired access tokens through the existing refresh API, and handles
errors centrally. No package/version changes were made.

Backend checks (from django_backend):

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py spectacular --validate --fail-on-warn
```

Browser smoke test (Node 22+, Chrome already installed; no new test dependency):

1. Start `django_backend/scripts/browser_fixture.py` with the backend virtualenv.
   It creates a disposable temporary database and starts port 8000. Do not run
   it on top of your existing backend process.
2. Start the frontend with `npm run dev -- --host 127.0.0.1 --port 5174 --strictPort`.
3. Start headless Chrome with a separate test user-data directory and
   `--remote-debugging-address=127.0.0.1 --remote-debugging-port=9223`.
4. From the workspace root, run `node frontend1/scripts/browser-smoke.mjs`.
   It checks real HTTP/UI flows, captures screenshots/results under
   `.work-audit/`, and never touches the real project database.
5. Stop the test processes when finished. Restart the disposable fixture for each
   fresh run. SMOKE_FRONTEND_URL and SMOKE_CDP_URL may override browser locations.

The existing frontend has no TypeScript typecheck command; Vite build and the
browser smoke test are the exercised frontend checks. The existing lint command
primarily covers JS/JSX, not all TSX code.

