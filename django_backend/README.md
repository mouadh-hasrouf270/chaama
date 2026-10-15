# Accounts and profiles API

CHAAMA business modules are now available under `/api/v1/`. Existing account and
JWT URLs remain unchanged. See [CHAAMA_API.md](CHAAMA_API.md) for routes, permissions,
booking setup and examples; [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md)
for validation and changed files; and [DEFERRED_FEATURES.md](DEFERRED_FEATURES.md)
for deliberately excluded Matter features and missing frontend pages.

This Django backend provides JWT authentication, lawyer profiles, practice areas,
and client records that may exist before their owners register.

## Run locally (PowerShell)

From `django_backend`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Interactive documentation: `/api/docs/`. OpenAPI schema: `/api/schema/`.
Use `/api/token/` with `username` and `password`, then send
`Authorization: Bearer <access>` on protected requests.

## Roles and access

- Public registration creates `CLIENT` accounts only. First name, last name,
  phone, username and password are required; email is optional.
- Administrators (`SUPER_ADMIN` or Django superusers) create privileged accounts
  through `POST /api/accounts/users/`.
- `INTERNAL_ASSOCIATE` and `EXTERNAL_SUBCONTRACTOR` are treated as lawyers.
  Creating either account automatically creates a lawyer profile. Administrators
  do not receive a lawyer profile automatically.
- Lawyers can read/update their own lawyer profile and create/read/update clients
  they created. Administrators can manage all profiles. Clients cannot access the
  staff client directory or other users' profiles.
- Clients read/update their own profile through `/api/accounts/clients/me/`.
  Internal `notes` and `created_by` are excluded from that endpoint.
- Practice areas can be read by authenticated accounts and modified by admins.
- Only admins can verify lawyers or confirm phone ownership. `is_verified`,
  `phone_verified`, profile ownership, and `created_by` cannot be set through
  ordinary profile updates.

## Client registration and linking

1. A lawyer/admin creates a client record with `POST /api/accounts/clients/`.
   It has no user account; `created_by` is taken from the authenticated caller.
2. The client registers with the same phone using `/api/accounts/register/`.
3. If the phone has no existing client record, a new profile is created and linked
   immediately. If it matches an existing record, that record is preserved and
   linking waits for ownership confirmation. `/api/accounts/me/` returns
   `client_link_pending: true`, and `/api/accounts/clients/me/` returns 404 until linked.
4. **After independently checking phone ownership**, an admin calls
   `POST /api/accounts/users/{user_id}/verify-phone/` with no body. This confirms
   ownership and links the existing client record without overwriting its names,
   notes, creator, or other details. Repeating the request is safe.

There is no SMS provider configured. Admin confirmation is the current trust
boundary: matching a submitted phone number alone never grants access to an
existing client's private record. The verification endpoint does not send SMS.

Phones must include the country code (`+213555123456` or `00213555123456`). Spaces,
parentheses, dots and hyphens are removed before matching. This validates the
international format, not whether the number actually exists. Phones are unique
within users and within client records. Changing an enrolled account phone is
not supported until a separate ownership/recovery flow is implemented.

Existing lawyer accounts receive profiles through the data migration. Existing
client accounts without a phone use `POST /api/accounts/me/phone/` with `phone`,
`first_name`, and `last_name`; this follows the same safe linking rules.

Deleting a user preserves its client record (`SET_NULL`) and deletes its lawyer
profile (`CASCADE`). Only admins can delete unlinked client records through the
API. Linked client records cannot be deleted independently through the API.
Role changes and bulk ORM updates are not exposed by this API; `bulk_create`
and `QuerySet.update` bypass the profile-creation signal and should not be used
to provision accounts.

## Endpoints

All paths below are relative to `/api/accounts/`.

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `register/` | Public client registration |
| GET | `me/` | Account, profile IDs, verification/link status |
| POST | `me/phone/` | Enroll phone for an older account without one |
| POST | `logout/` | Blacklist the submitted refresh token |
| GET, POST | `users/` | Admin lists/creates accounts |
| GET | `users/{id}/` | Admin reads an account |
| POST | `users/{id}/verify-phone/` | Admin confirms ownership and links client |
| GET, POST | `practice-areas/` | List/create practice areas |
| GET, PUT, PATCH, DELETE | `practice-areas/{id}/` | Read/update/delete practice area |
| GET | `lawyers/` | Admin: all; lawyer: own profile |
| GET, PUT, PATCH | `lawyers/{id}/` | Read/update an accessible lawyer profile |
| GET, PATCH | `lawyers/me/` | Own lawyer profile |
| PATCH | `lawyers/{id}/verification/` | Admin sets `is_verified` |
| GET, POST | `clients/` | List accessible clients/create offline client |
| GET, PUT, PATCH, DELETE | `clients/{id}/` | Manage accessible client |
| GET, PATCH | `clients/me/` | Client's own profile, without internal notes |

Lawyer list filters: `jurisdiction`, `is_verified`, `practice_areas` (ID).
Client list filter: `city`. IDs in lawyer detail URLs are **profile IDs**;
IDs in user URLs are **user IDs**. `/me/` provides both.

Lawyer profiles are created automatically, so there is no separate POST endpoint
to create a duplicate lawyer profile. They are removed with their user accounts.

## Example request bodies

Create an offline client (`POST clients/`, lawyer/admin):

```json
{
  "first_name": "Amine",
  "last_name": "Ben",
  "phone": "+213555123456",
  "email": "amine@example.com",
  "city": "Algiers",
  "notes": "Internal intake notes"
}
```

Register that client (`POST register/`, public):

```json
{
  "username": "amine",
  "password": "Example-only-strong-pass-938!",
  "first_name": "Amine",
  "last_name": "Ben",
  "phone": "+213555123456",
  "email": "amine@example.com"
}
```

To create a lawyer, an admin sends the same account fields to `POST users/`,
adding `"role": "INTERNAL_ASSOCIATE"` or `"role": "EXTERNAL_SUBCONTRACTOR"`.

Create a practice area (`POST practice-areas/`, admin):

```json
{"name": "Family law", "description": "Family-related legal matters"}
```

Update a lawyer profile (`PATCH lawyers/me/`, lawyer). Replace the practice area
ID with an existing ID; an empty list removes all assigned practice areas:

```json
{
  "bar_number": "BAR-2026-123",
  "bar_association": "Local Bar Association",
  "jurisdiction": "Algiers",
  "bio": "Family law practitioner",
  "years_experience": 5,
  "practice_areas": [1]
}
```

## Validation

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test apps.accounts
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py spectacular --validate --fail-on-warn
```

Existing development settings (including the hardcoded secret and `DEBUG=True`)
still need production configuration before deployment.
