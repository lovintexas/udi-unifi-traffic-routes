# UniFi Traffic Routes

PG3x plugin for controlling UniFi Network traffic routes from IoX.

## Configuration

Custom Parameters:

- `host` - UniFi console IP address, for example `192.168.1.1`
- `username` - Local UniFi administrator username
- `password` - Local UniFi administrator password

The plugin discovers UniFi traffic routes and creates an IoX node for each route.

Each route supports:

- Enable
- Disable
- Query

The route status reflects the UniFi `enabled` state.
