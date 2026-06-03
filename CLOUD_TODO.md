# Cloud TODO

## Data Persistence

Planned target:

- Supabase: persistent shared storage for local development and Streamlit Cloud.
- Schema file: `supabase/schema.sql`.
- Required Streamlit secrets: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
- Local JSON remains only as an offline fallback when Supabase secrets are missing.

## Admin Access

- The Streamlit cloud app currently exposes the admin tools as a normal `後台` tab.
- There is no separate admin route; admin tools are inside the Streamlit `後台` tab.
- Anyone who can open the public Streamlit app can potentially access the admin tab.

Needed before public launch:

- Add an admin gate using `st.secrets`.
- Require an admin password or token before showing admin controls.
- Hide or disable approve/reject/merge actions for non-admin users.

## Local vs Cloud Data

- Local and cloud should point at the same Supabase project when shared testing is desired.
- If Supabase secrets are missing, that runtime falls back to local `data/census.json`.

Needed:

- Make local development read/write the shared backend when desired.
- Keep a local-only fallback only for demo or offline testing.

## Streamlit Only

- `streamlit_app.py` is the only active app entry.
- The old HTML/CSS/JS local server version has been retired to avoid UI drift.
- F5 launches the Streamlit app.

## Public Launch Blockers

- Persistent storage is not ready.
- Admin access control is not ready.
- Edit-code protection is not implemented in the Streamlit cloud path.
- Delete/edit flows still need stronger ownership verification.
- Demo data mode still needs a cloud-safe implementation.

