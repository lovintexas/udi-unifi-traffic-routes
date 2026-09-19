# UniFi Traffic Routes

A PG3x plugin for Universal Devices IoX providing selected UniFi Network monitoring and control.

The plugin connects directly to a UniFi console using the local UniFi Network API and exposes supported UniFi objects as native IoX nodes for use in IoX programs, UD Mobile, status displays, and automation.

## Features

### Traffic Routes

- Automatically discovers UniFi Traffic Routes
- Creates an IoX node for each discovered route
- Displays current enabled/disabled state
- Enable a Traffic Route from IoX
- Disable a Traffic Route from IoX
- Query current route status
- Periodically polls UniFi so changes made outside IoX are reflected in IoX
- Changes only the `enabled` state of an existing Traffic Route

### UniFi Clients

Client nodes are created for clients placed in a UniFi Network client group named:

`IoX`

This allows selected clients to be exposed to IoX without creating nodes for every client known to UniFi.

For each selected client the plugin provides:

- Online/offline status
- Blocked status
- Block command
- Unblock command
- Query command
- Periodic status updates

Online status and blocked status are intentionally independent.

A blocked client normally disappears from UniFi's active-station list. It is therefore valid for a client to report:

- Status: Offline
- Blocked: True

Unblocking a client permits it to reconnect but does not force the client to immediately associate with the network. Online status remains Offline until UniFi sees the client again.

Block and Unblock commands use delayed readback of UniFi's actual blocked-client state rather than assuming that a command succeeded.

### Switch Ports

The plugin discovers physical ports on supported UniFi switches.

For each switch port it provides:

- Link status
- Negotiated link speed

Port node names include both the port name and switch name where available.

### PoE Switch Ports

PoE-capable ports provide additional monitoring and control:

- Link status
- Link speed
- Configured PoE enabled state
- Current PoE power
- PoE On
- PoE Off
- PoE Cycle

PoE Enabled represents the configured state of the port.

A port configured for PoE may not currently be delivering power if no powered device is attached. For this reason, instantaneous power delivery alone is not used to determine whether PoE is enabled.

PoE commands use delayed readback from the switch.

PoE Cycle:

1. Turns PoE off
2. Verifies the state
3. Waits briefly
4. Restores automatic PoE
5. Verifies the resulting state

### Firewall Policies

The plugin discovers user-created UniFi firewall policies.

For each supported policy it provides:

- Enabled/disabled status
- Enable
- Disable
- Query

Only policies reported by UniFi with:

`predefined = false`

are exposed.

UniFi system/predefined policies are deliberately excluded.

The plugin changes only the enabled state of a firewall policy. It does not modify:

- Policy action
- Source
- Destination
- Networks
- Ports
- Matching criteria
- Other firewall policy configuration

## Requirements

- Universal Devices eisy running PG3x
- UniFi Network application
- UniFi console accessible from the eisy
- Local UniFi user account with sufficient permissions for the functions being used

The plugin has been developed and tested with a Ubiquiti UDM Pro.

## UniFi Configuration

### Local User

Create a dedicated local UniFi user for the plugin rather than using your primary UniFi administrator account.

In the UniFi console, configure the account as:

- **Account Type:** Admin
- **Network:** Full Admin
- **Local Account Only:** Enabled

The plugin requires Network administrative access because it performs both read and write operations, including Traffic Route control, client Block/Unblock, PoE control, and firewall policy enable/disable.

Permissions for other UniFi applications such as Protect, Access, Talk, and Control Plane are not required by this plugin.

Using a dedicated local account allows its credentials and permissions to be managed independently from your normal UniFi administrator account.

### IoX Client Group

To expose selected UniFi clients to IoX, create a UniFi Network client group named:

`IoX`

The group must be of type:

`CLIENTS`

Add each client that should appear as an IoX node to this group.

This prevents the plugin from creating IoX nodes for every client UniFi has ever discovered.

## PG3x Configuration

Configure the following Custom Parameters:

- `host` - IP address or hostname of the UniFi console, for example `192.168.1.1`
- `username` - Local UniFi username
- `password` - Local UniFi password

After the parameters are saved, the plugin authenticates with the local UniFi console, discovers supported objects, and creates or updates the corresponding IoX nodes.

If initial authentication fails, the controller is marked unavailable.

The plugin intentionally does not continuously retry failed authentication on every poll. Correcting the Custom Parameters or restarting the plugin initiates another authentication attempt.

## IoX Nodes

### Controller

Represents the plugin connection and operational state.

### Traffic Route

Provides:

- Enabled status
- Enable
- Disable
- Query

### UniFi Client

Provides:

- Online/offline Status
- Blocked status
- Block
- Unblock
- Query

### Switch Port

Provides:

- Link status
- Link speed

### PoE Switch Port

Provides:

- Link status
- Link speed
- PoE Enabled
- PoE power
- PoE On
- PoE Off
- PoE Cycle

### Firewall Policy

Provides:

- Enabled status
- Enable
- Disable
- Query

## Polling and Discovery

The plugin uses separate polling intervals for routine status updates and discovery.

The default configuration is:

- Short Poll: 30 seconds
- Long Poll: 300 seconds

PG3x may retain polling values already configured for an installed instance.

Short polling updates operational state such as:

- Traffic Route state
- Selected client online state
- Selected client blocked state
- Firewall policy state
- Switch-port state
- PoE state and power

Long polling performs discovery so newly available supported objects can be added.

Commands that require verification perform their own delayed readback and normally do not need to wait for the next regular polling cycle.

## Status Behavior

### Client Online Status

Client online status is obtained from UniFi's active-station data.

If a client is not present in the active-station list, it is reported Offline.

A sleeping, disconnected, or blocked device may therefore report Offline.

### Client Blocked Status

Blocked status is obtained separately from UniFi's blocked-client information.

This allows the plugin to distinguish between:

- A client that is simply offline
- A client that has been explicitly blocked

### PoE Status

PoE Enabled represents configured PoE state rather than merely whether power is currently being consumed.

PoE power reports current measured power where UniFi supplies that information.

## Design Boundaries and Limitations

### Not a General UniFi Configuration Editor

The plugin intentionally exposes a limited set of well-defined operations.

It is not intended to reproduce the UniFi Network administration interface inside IoX.

### Ordinary Switch-Port Disable Is Not Implemented

Administrative enable/disable of ordinary non-PoE switch ports is deliberately not implemented.

Testing showed that the current UniFi interface changes several network/VLAN-related port configuration fields rather than exposing a simple independent port-enable flag.

Automatically manipulating those fields could unintentionally alter port configuration, so this operation is omitted.

### Firewall Editing Is Restricted

Only user-created firewall policies are exposed.

Only their enabled state can be changed.

The plugin does not provide general firewall-rule editing.

### Client Scope Is Explicit

Only clients assigned to the UniFi `IoX` client group are exposed as client nodes.

### Online and Blocked Are Separate States

Unblocking a client permits network access but does not cause the device to immediately reconnect.

A client may therefore remain Offline for some time after being unblocked.

### Discovery Is Additive

Discovery creates nodes for supported objects.

Removing an object from UniFi or removing a client from the `IoX` group does not necessarily delete an existing IoX node automatically.

Automatic stale-node deletion is not currently a design goal.

### UniFi API Compatibility

The plugin uses local UniFi Network API endpoints observed and tested against the development environment.

Some of these interfaces are not guaranteed to remain unchanged between UniFi Network releases.

A future UniFi update may therefore require plugin changes.

### TLS Certificate Verification

TLS certificate verification is disabled for the local UniFi connection in the current implementation.

This accommodates locally addressed UniFi consoles using their appliance certificate, but means the plugin does not independently validate the server certificate.

## Local API Operations

The following endpoints are implementation details and are listed primarily for technical reference and troubleshooting.

### Authentication

`POST /api/auth/login`

Authentication uses the UniFi session cookie and CSRF token.

### Traffic Routes

`/proxy/network/v2/api/site/default/trafficroutes`

### Client Groups

`/proxy/network/v2/api/site/default/network-members-groups`

### Active Clients

`/proxy/network/api/s/default/stat/sta`

### Blocked Clients

`/proxy/network/v2/api/site/default/clients/history?onlyBlocked=true&withinHours=0`

### Block / Unblock Client

`POST /proxy/network/api/s/default/cmd/stamgr`

Commands:

- `block-sta`
- `unblock-sta`

### Switch and Port Status

`/proxy/network/api/s/default/stat/device`

### PoE Configuration

PoE control updates the switch device using its existing port override configuration while changing the target port's `poe_mode`.

### Firewall Policies

Read policies:

`/proxy/network/v2/api/site/default/firewall-policies`

Enable/disable policies:

`/proxy/network/v2/api/site/default/firewall-policies/batch`

## Security

Use a dedicated local UniFi account with a strong unique password.

Do not publish:

- UniFi passwords
- Session cookies
- CSRF tokens
- Authentication headers
- Other authentication credentials

PG3x DEBUG logging may expose Custom Parameters. Normal operational logging should therefore be kept below DEBUG after development and troubleshooting are complete.

If credentials have appeared in development/debug logs, rotating the dedicated UniFi password is recommended.

## Additional Documentation

A formatted HTML version of the plugin documentation is included in the repository:

[PLUGIN_GUIDE.html](PLUGIN_GUIDE.html)

## License and Notice

See `NOTICE` for applicable notices.

---

UniFi is a product family of Ubiquiti Inc. This plugin is an independent integration and is not an official Ubiquiti product.
