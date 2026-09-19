# UniFi Traffic Routes

A PG3x plugin for Universal Devices IoX that provides control and status of UniFi Network Traffic Routes.

The plugin connects directly to a UniFi console using the local UniFi Network API, discovers configured Traffic Routes, and creates an IoX node for each route.

## Features

- Automatically discovers UniFi Traffic Routes
- Creates an IoX node for each discovered route
- Enable a Traffic Route from IoX
- Disable a Traffic Route from IoX
- Query current route status
- Periodically polls UniFi so changes made outside IoX are reflected in IoX
- Automatically re-authenticates when the UniFi session expires
- Changes only the `enabled` state of an existing Traffic Route

## Requirements

- Universal Devices eisy running PG3x
- UniFi Network application
- UniFi console accessible from the eisy
- Local UniFi user account with sufficient permission to view and modify Traffic Routes

This plugin has been developed and tested with a Ubiquiti UDM Pro.

## UniFi Configuration

Create a local UniFi user for the plugin rather than using your primary UniFi account.

The account must have sufficient permissions to:

- Read Traffic Routes
- Modify Traffic Routes

Using a dedicated account allows its credentials and permissions to be managed independently from your normal UniFi administrator account.

## PG3x Configuration

Configure the following Custom Parameters:

- `host` - IP address or hostname of the UniFi console, for example `192.168.1.1`
- `username` - Local UniFi username
- `password` - Local UniFi password

After the parameters are saved, the plugin connects to UniFi and discovers the configured Traffic Routes.

## IoX Nodes

The plugin creates one child node for each UniFi Traffic Route.

Each Traffic Route node supports:

- **Enable** - Enables the Traffic Route
- **Disable** - Disables the Traffic Route
- **Query** - Retrieves the current state

The node status represents the UniFi Traffic Route `enabled` state.

Traffic Routes themselves should be created and configured in UniFi. The plugin controls whether an existing route is enabled or disabled; it does not create or modify the route's routing configuration.

## Polling

The plugin periodically retrieves Traffic Route status from UniFi.

This means a route enabled or disabled directly through the UniFi interface will subsequently be reflected in IoX.

## Authentication

The plugin authenticates directly with the UniFi console and maintains a local authenticated session.

If the session expires, the plugin can authenticate again. A failed initial login does not continuously retry on every polling cycle, preventing repeated authentication attempts from locking the UniFi account.

## License

See `NOTICE` for license information.
