# hOn Integration for Home Assistant

This is a custom component for Home Assistant to integrate with Haier hOn appliances.
This version includes fixes and improvements over the original repository, specifically targeting stability and enhanced control for climate devices.

## Key Improvements

### 🛠️ Stability
- **Network Timeouts**: Added a 30-second timeout to API requests to prevent Home Assistant from hanging indefinitely when hOn servers are unresponsive.

### ❄️ Climate Control
- **Advanced Flap Control**: Added specific vertical swing positions (`High`, `Mid-High`, `Mid-Low`, `Low`) for precise airflow control.
- **Optimistic UI Updates**: Implemented "optimistic" state updates. When you change settings (temp, mode, fan), the UI updates immediately and waits for the confirmation, fixing the annoying "flickering" effect where controls would jump back to the old state.
- **Bug Fixes**: Fixed issues with integer/string type conversions for command parameters.

## Installation

1. Copy the `custom_components/hon` directory to your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Add the integration via the UI.

## Credits

Based on the work by [gvigroux](https://github.com/gvigroux/hon).
