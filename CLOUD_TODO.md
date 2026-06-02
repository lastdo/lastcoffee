# Cloud TODO

## Data Persistence

- Streamlit Cloud currently writes survey state to `data/census.json` inside the app container.
- This is not reliable long-term storage. Reboot, redeploy, or platform resource recycling may lose local file changes.
- Before public launch, move shared state to a persistent external data source.

Recommended options:

- Google Sheets: easiest for manual inspection and small community data.
- Supabase: better if we want database-style querying, auth, and admin tools.
- Firestore: good managed document store, but setup is heavier.

## Admin Access

- The Streamlit cloud app currently exposes the admin tools as a normal `後台` tab.
- Unlike the local HTML version, there is no `/lastcoffee/admin` route or `?admin` gate.
- Anyone who can open the public Streamlit app can potentially access the admin tab.

Needed before public launch:

- Add an admin gate using `st.secrets`.
- Require an admin password or token before showing admin controls.
- Hide or disable approve/reject/merge actions for non-admin users.

## Local vs Cloud Data

- Local runs against the local `data/census.json`.
- Streamlit Cloud runs against its own deployed/container-side `data/census.json`.
- Local admin approval does not modify cloud-submitted pending brands.

Needed:

- Use the same external data source for both local and cloud.
- Make local development read/write the shared backend when desired.
- Keep a local-only fallback only for demo or offline testing.

## Streamlit / HTML Version Sync

- Cloud uses `streamlit_app.py`.
- Local HTML/server mode uses `index.html`, `app.js`, `styles.css`, and `server.py`.
- Recent features must be mirrored between both versions, or the cloud UI and local UI will diverge.

Current synced features:

- Records page with grouped Bahamut IDs.
- Record detail dialog titled `器材火力展示!`.
- Clear pending-brand entry hint.
- Pending-brand statistics separation.
- Admin approve/reject/merge flow.

Ongoing risk:

- Any new feature added to one UI must be explicitly ported to the other unless we retire one version.

## Public Launch Blockers

- Persistent storage is not ready.
- Admin access control is not ready.
- Edit-code protection is not implemented in the Streamlit cloud path.
- Delete/edit flows still need stronger ownership verification.
- Demo data mode still needs a cloud-safe implementation.

