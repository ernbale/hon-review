# hOn Integration: Technical Deep Dive & Context

This document serves as a technical reference to understand the specific modifications, architectural decisions, and logic implemented in this fork of the `hon` integration.

## 1. Core Stability Patch (`hon.py`)
**Problem**: The original integration relied on the default `aiohttp` configuration, which has no explicit timeout for some operations, or a very long one. The hOn servers are notoriously unstable, leading to "hanging" connections that blocked the entire Home Assistant update loop.
**Solution**:
- In `HonConnection.__init__`, we explicitly injected a `ClientTimeout(total=30)` into the `aiohttp.ClientSession`.
- **Code Reference**:
  ```python
  timeout = aiohttp.ClientTimeout(total=30)
  self._session = aiohttp.ClientSession(..., timeout=timeout)
  ```

### 1.1 Auto Re-Authentication After a Network/DNS Blip (v1.0.8)
**Problem**: After a transient network or DNS outage (the hOn cloud lives on AWS `api-iot.he.services`), the cloud often invalidates the session token. The original `async_get_context` only re-authenticated on a fixed 6-hour `SESSION_TIMEOUT`; in between it sent the GET **without checking the HTTP status** and did `data.get("payload", {})`. A `401` therefore became an empty `{}`, which `device.load_context()` swallows silently (`no shadow data in: {}`) and `_async_update_data` returns `None` with **no exception**. The coordinator considers the update "successful" and keeps reusing the dead token every 60s — the integration stays *down* until a manual reload re-creates the connection.
**Solution**:
- Split the fetch into `_fetch_context()` which inspects `response.status`: a non-200 returns `None` (signal "auth probably stale"), while transport errors (DNS/connection) are left to propagate so HA handles them as `UpdateFailed` (native retry).
- `async_get_context()` now: on a `None` result, re-authenticates **once** and retries the fetch. `async_authorize()` already tries the saved token first and falls back to the full OAuth login if it's dead.
- An `asyncio.Lock` (`self._auth_lock`) serializes re-auth so the parallel per-device coordinators don't trigger N simultaneous logins; tasks that lose the race re-check the fetch before forcing a new login.
- **Net effect**: a blip no longer requires a manual reload — the integration recovers on its own within one or two update cycles.

### 1.2 CIAM / unified-api Login Migration (v1.0.9)
**Problem**: Around 2026-06-15 Haier retired the auth flow this integration depended on. All entities went `unavailable`. Two things broke:
1. The **Salesforce Aura → OAuth2** login (`/s/sfsites/aura`, `/apex/ProgressiveLogin`, `/services/oauth2/authorize`).
2. The **`GET /commands/v1/appliance`** list endpoint — it still returns `200`, but with an **empty** `appliances: []`, so no entities are created (silently, no error logged). This is exactly what was observed: config entry `loaded`, but every `climate.clima_*` left as `restored/unavailable`.
**Root cause**: the cloud moved to a **CIAM/PKCE** auth flow and reads appliances from a new **unified-api** endpoint. The per-appliance endpoints (`context`, `retrieve`, `statistics`, `send`) are **unchanged** and keep working with the new tokens.
**Solution** (ported from upstream gvigroux 0.8.3, PR #323, preserving our timeout + auto-reconnect work):
- **Auth** → `GET /ciam/authorize` (username/password + PKCE S256 `code_challenge`) → `session_id`, then `POST /ciam/token` (`session_id` + `code_verifier`) → `{cognito_token, id_token, refresh_token}`. Removes the Aura/OAuth chain, `client_id`, `redirect_uri` and the `fwuid` framework dance (`CONF_FRAMEWORK` left defined but unused; `async_get_frontdoor_url` and `async_try_saved_token` removed).
- **Appliance list** → `POST /unified-api/v1/view/appliance-list {"deviceId": "homeassistant"}`, parsing `modules.applianceList.payload.appliances`.
- **`SESSION_TIMEOUT` lowered to 600s** (CIAM tokens expire after ~15 min). `_ensure_session()` re-auths under `_auth_lock` before each context/set/send when stale.
- **Kept our additions**: `ClientTimeout(total=30)`, `_auth_lock`, and the robust `_fetch_context`/`async_get_context` retry-on-non-200 from §1.1.
- `const.py`: `APP_VERSION` `2.0.10` → `2.27.9`.
**Gotcha**: the API authorizer reads `cognito-token` / `id-token` **case-sensitively (lowercase)**. `aiohttp` sends them lowercase as written, so it's fine — a `urllib`-based client that title-cases headers gets a misleading `403 "explicit deny in an identity-based policy"`.
**Verified live** (2026-06-17): all 6 climates load with live `current_temperature`/target via the context poll.

## 2. Climate Entity Logic (`climate.py`)
The `HonClimateEntity` class required significant overriding to handle the specific capabilities of this user's AC model.

### 2.1 Vertical Swing Mapping
The standard hOn API uses generic enums. This model supports specific vertical positions which were reverse-engineered.
- **Mapping Dictionary**: `SWING_VERTICAL_MAP` maps string UI representations to raw API integers.
  - `alto` -> `2`
  - `medio_alto` -> `4`
  - `medio_basso` -> `5`
  - `basso` -> `6`
- **Logic**: In `async_set_swing_mode`, we check if the requested mode is in this map. If so, we bypass the standard `SWING_BOTH`/`AUTO` logic and send the direct integer value via `windDirectionVertical`.

### 2.2 Optimistic UI Updates
**Problem**: "Flickering". The API is slow. Sending a command (e.g., "Set Cool") takes seconds. The default behavior reads the state *immediately* after sending, but the server hasn't updated yet, so the UI reverts to "Off", then jumps back to "Cool" later.
**Solution**:
- **Watcher Logic**: `self._watcher` is a mechanism (likely polled) to check updates.
- **Intervention**: We added specific logic (e.g., `self.start_watcher()`) or modified `_handle_coordinator_update`:
  ```python
  # If a watcher/operation is in progress, ignore incoming state updates from the coordinator
  if self._watcher is not None:
      return
  ```
- This prevents the "old" server state from overwriting the "new" tentative local state while a command is processing.

## 3. Custom HACS Structure
Original repository had a flat structure (all files in root).
**Standard**: `custom_components/hon/`
**Action Taken**:
- Renamed/Moved all functional python files.
- Kept `README.md` in root.
- This ensures `hacs.json` or automatic HACS discovery works correctly without custom path configuration.

## 4. Specific "Reload" Capability
**Feature**: Force Reload.
**Implementation**:
- Likely leveraging `button.py` or `config_flow` reconfigure hooks.
- **User Request**: Added a button to manually trigger `async_update_entry` or similar to clear stale cache/state from the unstable hOn API.

## 5. Future Maintenance
- **Watch out for**: `HonParameterRange` objects in `climate.py`. If the API schema changes for temperature steps, the `get` logic might fail.
- **Authentication**: Uses a standard user/password flow (likely in `config_flow.py`). If hOn changes auth (e.g., 2FA), this will break.

## 6. HACS Distribution & Releasing
To ensure this integration works with HACS as a custom repository:
1.  **`hacs.json`**: Required at root.
    ```json
    {
      "name": "hOn review",
      "render_readme": true,
      "filename": "hon.zip",
      "hide_default_branch": true
    }
    ```
2.  **Manifest Versioning**: `manifest.json` MUST have a valid "version" key (e.g., "1.0.1"). HACS often fails if this is missing or invalid.
3.  **Git Tags**: HACS looks for GitHub Releases/Tags.
    - Workflow: Commit changes -> `git tag v1.0.X` -> `git push origin v1.0.X`.
    - This forces HACS to see a new update available.
