# Changelog

## 1.1.3

- Removed duplicate PoE On and PoE Off commands from PoE switch-port nodes.
- PoE Enable/Disable controls now use the standard On/Off commands, providing a cleaner interface and native toggle control in UD Mobile.
- Updated plugin version and profile version.

## 1.1.2

- Fixed UniFi switch and port node hierarchy.
- UniFi switch ports are now grouped under their corresponding switch.
- Improved node creation reliability and handling of failed node additions.
- Changed the default controller name to UniFi Control.

## 1.1.0

- Improved UniFi Client and PoE port integration with IoX and UD Mobile.
- Client Blocked state and PoE Enabled state are now the primary node states, allowing standard On/Off controls to work naturally.
- Added On/Off mappings for Block/Unblock and PoE On/Off.
- Fixed PoE control for ports that do not already have a UniFi port override.
- Updated documentation.

## 1.1.0

- Added discovery and monitoring of UniFi Wi-Fi SSIDs.
- Added Enable, Disable, and Query commands for SSIDs.
- SSID status changes made in UniFi are reflected in IoX through polling.
- SSID control preserves the existing WLAN configuration and changes only its enabled state.
- Updated plugin documentation.

## 1.0.0

- Initial release.
- UniFi Traffic Route monitoring and enable/disable control.
- Selected client monitoring using the IoX client group.
- Client Block/Unblock control with independent blocked-state reporting.
- UniFi switch-port status and link-speed monitoring.
- PoE status, power monitoring, On/Off, and PoE Cycle control.
- User-created firewall-policy monitoring and enable/disable control.
