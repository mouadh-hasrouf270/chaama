# Deferred features / fonctionnalités différées

These omissions are intentional. No Matter model, MatterAssignment, nullable
placeholder matter field, or Matter CRUD was introduced.

| Feature | Reason deferred | Dependency | Future integration point |
| --- | --- | --- | --- |
| Matters, assignments, parties, notes, contact logs, timeline | Explicitly excluded from this phase | Matter design and permission policy | New dedicated matter app |
| Matter documents and versions | Must inherit access from a real matter | Matter/document ownership | Separate document service; do not reuse intake evidence as matter documents |
| Hearings and deadlines | Need case relationships and visibility | Matter | Extend calendar aggregation after matter permissions exist |
| Matter tasks | Need case assignment and responsibility | Matter | Extend dashboard and tasks API |
| Fee agreements, invoices, billing | Need matter/engagement financial rules | Matter | Billing services after matter scope is agreed |
| Delegations and linked opportunities | Need the underlying legal engagement | Matter / Delegation | Dedicated delegation workflow |
| Milestones, submissions, retrocession | Need delegation and fee rules | Delegation | Financial and delivery workflows |
| Matter/delegation conversations | Need scoped participants | Matter / Delegation | Authorized messaging service |
| Automatic Matter creation on assistance acceptance | Explicitly excluded | Matter | Commented future hook in assistance/services.py |
| Conflict search in MatterParty | That model does not exist | MatterParty | Extend search_existing_parties() sources |

## Missing frontend pages

The supplied React tree has no dedicated organizations, practice-area management,
lawyer directory, partner directory, assistance request, audit, fees, or insights
pages. No new pages, routes, design system or CSS were invented.

- Organizations and memberships are managed in Django admin. No unused organization
  REST CRUD was added.
- Practice areas and lawyers reuse existing account administration. Their public
  APIs exist and are consumed by Home/booking as applicable.
- LegalInsight and PublicFee models/APIs are deferred because the specification
  made them conditional on existing pages; neither page exists in this repository.
- Partner/assistance/audit backend APIs are complete and documented in Swagger;
  their dedicated frontend integration awaits those pages.
- There is no standalone intake/evidence page. The existing public booking flow
  submits intake atomically. Authenticated evidence upload/download APIs are
  available; no upload controls were added to the approved booking design.
- There is no client create/edit form or modal: only an inert “Nouveau client”
  button. Client CRUD is available through the API; that button stays in place,
  disabled with an explanatory title. No form was invented.
- The existing profile form can display the account and save practice-area
  selections. Account-name/email updates, avatar persistence and password changes
  have no existing backend endpoints and would extend the excluded Accounts/Auth
  scope. Those controls are read-only/disabled, not simulated.
- Partner signup, activation and password-reset forms already contain mock behavior.
  They were not connected or rewritten because Accounts/Auth is excluded. Only
  the login/logout integration required for real authenticated data was connected
  to the existing JWT endpoints.
- Existing Matters, Tasks and Billing pages remain unchanged mock prototypes.
  They are not represented as connected features. Dashboard, clients and calendar
  no longer borrow their invented case/task/hearing data.
- The calendar preserves its existing Monday–Friday visual layout; weekend
  availability is supported by the API but a weekend calendar layout is deferred.
- Home's unsupported historic experience/case/satisfaction statistics display
  “—”; the verified-lawyer count comes from the public directory. Approved
  descriptive/marketing text remains static content.

