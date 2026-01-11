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
