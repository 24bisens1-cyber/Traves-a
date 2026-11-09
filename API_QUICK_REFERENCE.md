# API quick reference

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/health` | Service and database health |
| GET | `/api/capabilities` | Module/provider capabilities |
| POST | `/api/companion/chat` | Optional server-side AI chat with local fallback |
| POST | `/api/media/clip-storyboard` | Authenticated + CSRF + consent-gated frame storyboard |
| POST | `/api/auth/register` | Register member |
| POST | `/api/auth/login` | Establish session |
| GET | `/api/auth/me` | Current session and CSRF token |
| POST | `/api/auth/logout` | Revoke current session |
| POST | `/api/travel/flights/offers` | Authorised Amadeus offers or explicit external hand-offs |
| GET | `/api/travel/weather` | Source-labelled current/forecast data |
| GET | `/api/maps/config` | NASA GIBS / optional MapTiler tile configuration |
| GET | `/api/providers/status` | Provider configuration readiness |
| POST | `/api/budget/allocate` | Illustrative budget allocation |
| POST | `/api/trip/fit` | Explainable destination-fit heuristic |
| POST | `/api/scenarios/run` | Illustrative travel scenario |
| POST/GET/PUT | `/api/shared-trips` | Create/read/update shared trips; edits require the correct editor token |

Legacy Civic Pulse endpoints are not part of this release.
