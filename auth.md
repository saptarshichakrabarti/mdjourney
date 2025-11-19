# Local Development Setup Checklist

*(RBAC + SQLite Identity Store + JWT Auth + Refresh Tokens)*
**No code included. All developer actions only.**

---

## 1. Workspace and Environment Preparation

* [ ] Create or switch to a dedicated development branch.
* [ ] Create the directory structure for the auth system:

  * `auth/data/` for runtime DB and dev keys
  * `auth/migrations/` for schema files
  * `auth/scripts/` for local initialization and migration tools
* [ ] Add `auth/data/*` to `.gitignore` (DB file, dev keys, and any YAML snapshots).
* [ ] Ensure your Python environment or container is isolated and ready.
* [ ] Document that this setup is **development-only** and not production-safe.

---

## 2. Initialize SQLite Identity Store (ACID, local-only)

* [ ] Create an empty SQLite database file at `auth/data/mdjourney.db`.
* [ ] Apply the schema in `auth/migrations/001_init.sql`:

  * Includes tables: `users`, `user_global_roles`, `user_resource_roles`,
    `refresh_tokens`, `api_keys`, `revoked_tids`, and `audit_index`.
* [ ] Confirm SQLite is operating in WAL mode with full synchronous settings.
* [ ] Run a basic DB integrity check (`PRAGMA integrity_check`) to confirm correctness.
* [ ] Create a backup copy of the empty DB for safety (local only).

---

## 3. Prepare for Migration from YAML

* [ ] Locate `.mdjourney_users.yaml` from your existing system.
* [ ] Copy it to a safe snapshot location outside of your project folder.
* [ ] Identify the YAML sections for users, global roles, resource roles, API keys, and refresh tokens.
* [ ] Decide how YAML fields map to DB rows:

  * YAML → DB fields should be documented before migration.

---

## 4. Dry-Run Migration (simulate import)

* [ ] On a **copy** of the SQLite DB, perform a trial import:

  * Confirm user count matches YAML.
  * Confirm global and resource roles map correctly.
  * Confirm API keys appear with correct user associations.
  * Confirm refresh tokens appear as **hashed values**, not plaintext.
* [ ] Validate referential integrity (every user ID referenced is valid).
* [ ] Confirm no unexpected entries and no conversion issues.

---

## 5. Execute the Real Migration (one-time import)

* [ ] Run the actual import on the **real** SQLite DB inside a single transaction.
* [ ] Verify the following after commit:

  * All users are present.
  * All role assignments exist.
  * All API keys were imported.
  * All refresh tokens were hashed and stored.
* [ ] Immediately rename the YAML file to something like `mdjourney_users.yaml.migrated`.
* [ ] Move the renamed YAML to a secure offline folder.
* [ ] Plan to force rotation of all imported API keys and refresh tokens after initial system bring-up.

---

## 6. Generate Local Development Signing Keys

* [ ] Create a development-only RSA private key and corresponding public key.
* [ ] Store both inside `auth/data/`.
* [ ] Set permissions so only the development user can read them.
* [ ] Note clearly in README that these keys must never be used in production.

---

## 7. Bring Up the Local Auth Service (development edition)

* [ ] Configure the auth service to:

  * Read the private key for signing JWT access tokens.
  * Read the public key for JWKS exposure and local validation.
  * Use the SQLite DB for users, API keys, roles, refresh tokens, and revocations.
  * Issue short-lived access tokens (5–15 minutes).
  * Create and rotate refresh tokens on each `/auth/refresh` call.
  * Mark old refresh tokens as revoked after rotation.
  * Support simple login, refresh, logout, and RBAC resolution endpoints.
* [ ] Start the auth service locally (e.g., with a development server).
* [ ] Confirm the following endpoints respond correctly:

  * `/auth/login`
  * `/auth/refresh`
  * `/auth/logout`
  * `/auth/jwks`
  * (optional) user and role management endpoints for local testing.

---

## 8. Backend Integration (metadata API)

* [ ] Update the metadata API to accept `Authorization: Bearer <access_token>` on incoming requests.
* [ ] Validate access tokens by:

  * Verifying the JWT signature using the **public key**.
  * Checking token expiry.
  * Checking the token ID (`tid`) against `revoked_tids` for immediate revocation.
* [ ] For resource-scoped permission checks, call the auth service’s RBAC resolution endpoint or consult resource roles directly.
* [ ] Document required permissions for each protected endpoint.
* [ ] Add audit logging for permission decisions and important actions.

---

## 9. Frontend Integration (local development)

* [ ] Implement login flow:

  * Call `/auth/login`.
  * Store the returned access token **in memory only**.
  * Allow the browser to store the refresh token as an **HttpOnly, SameSite=Strict** cookie.
* [ ] Attach the access token to all API requests via `Authorization: Bearer …`.
* [ ] On 401 errors (expired access token), call `/auth/refresh`:

  * The browser automatically sends the refresh token cookie.
  * Replace the access token in memory with the new one.
  * Retry the failed request.
* [ ] Implement simple CSRF protection for any cookie-based interactions (double-submit token).
* [ ] Confirm the frontend can:

  * Log in
  * Fetch resources
  * Refresh tokens
  * Handle expired tokens gracefully

---

## 10. Audit Logging and Integrity (local-only baseline)

* [ ] Ensure the auth service writes audit events to a local, append-only log file.
* [ ] Create a brief index entry in the `audit_index` table for each event.
* [ ] Maintain a simple integrity mechanism (e.g., running hash of entries).
* [ ] Periodically verify logs are being written and indexed.

---

## 11. Testing & Verification (required)

* [ ] **Token lifecycle tests**

  * Issue a token.
  * Confirm valid access for its lifetime.
  * Confirm refresh works and rotates the refresh token.
* [ ] **RBAC tests**

  * Test global roles (admin / editor / viewer).
  * Test resource-scoped roles with a couple of sample datasets.
* [ ] **Migration verification**

  * Confirm imported users can successfully log in.
  * Confirm imported roles produce the correct access decisions.
* [ ] **Revocation tests**

  * Manually revoke a token ID.
  * Confirm immediate access denial for that token.
* [ ] **Concurrency tests**

  * Perform two refresh requests simultaneously for the same refresh token.
  * Expected result: exactly one succeeds; the other fails due to rotation.
* [ ] **Backup & restore**

  * Copy the DB file.
  * Delete the live one.
  * Restore from backup.
  * Confirm auth behavior resumes normally.

---

## 12. Cleanup, Documentation, and Rotation (end of local setup)

* [ ] Rotate all API keys imported from the YAML file.
* [ ] Rotate all refresh tokens imported from YAML.
* [ ] Update README with:

  * How to initialize DB
  * How to migrate from YAML
  * How to run the local auth service
  * How the frontend authenticates and refreshes tokens
  * What artifacts must never be committed
  * A reminder that dev keys, dev-only cookies, and plaintext traffic must be replaced before production
* [ ] Confirm the team understands which steps change for production (e.g., Vault/KMS for keys, TLS, Redis cache, full audit hash-chains).

---

## API Documentation

This section documents the API endpoints for the authentication system.

### Create User

* **URL:** `/users/`
* **Method:** `POST`
* **Body:**

```json
{
  "username": "string",
  "password": "string",
  "email": "user@example.com",
  "full_name": "string",
  "disabled": false
}
```

* **Response:**

```json
{
  "username": "string",
  "email": "user@example.com",
  "full_name": "string",
  "disabled": false
}
```

### Login for Access Token

* **URL:** `/auth/token`
* **Method:** `POST`
* **Body:**

```bash
username=string&password=string
```

* **Response:**

```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```
