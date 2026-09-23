#!/usr/bin/env python3

import sys
import time
import threading
import requests
import urllib3
import udi_interface

LOGGER = udi_interface.LOGGER
Custom = udi_interface.Custom

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class UniFiClient:
    def __init__(self, host, username, password):
        self.host = host.rstrip("/")
        self.username = username
        self.password = password

        self.session = requests.Session()
        self.session.verify = False

        self.base = (
            f"https://{self.host}"
            "/proxy/network/v2/api/site/default/trafficroutes"
        )

    def login(self):
        LOGGER.info("Logging into UniFi at %s", self.host)

        response = self.session.post(
            f"https://{self.host}/api/auth/login",
            json={
                "username": self.username,
                "password": self.password
            },
            timeout=15
        )

        response.raise_for_status()

        csrf = (
            response.headers.get("x-updated-csrf-token")
            or response.headers.get("x-csrf-token")
        )

        if not csrf:
            raise RuntimeError("UniFi login succeeded but no CSRF token returned")

        self.session.headers.update({"X-Csrf-Token": csrf})

        LOGGER.info("UniFi login successful")

    def get_routes(self):
        response = self.session.get(self.base, timeout=15)

        if response.status_code in (401, 403):
            self.login()
            response = self.session.get(self.base, timeout=15)

        response.raise_for_status()
        return response.json()

    def get_client_groups(self):
        url = (
            f"https://{self.host}"
            "/proxy/network/v2/api/site/default/network-members-groups"
        )

        response = self.session.get(url, timeout=15)

        if response.status_code in (401, 403):
            self.login()
            response = self.session.get(url, timeout=15)

        response.raise_for_status()
        return response.json()

    def get_clients(self):
        url = (
            f"https://{self.host}"
            "/proxy/network/api/s/default/stat/sta"
        )

        response = self.session.get(url, timeout=15)

        if response.status_code in (401, 403):
            self.login()
            response = self.session.get(url, timeout=15)

        response.raise_for_status()

        data = response.json()
        return data.get("data", [])

    def get_blocked_clients(self):
        url = (
            f"https://{self.host}"
            "/proxy/network/v2/api/site/default/clients/history"
        )

        response = self.session.get(
            url,
            params={
                "onlyBlocked": "true",
                "withinHours": 0
            },
            timeout=15
        )

        if response.status_code in (401, 403):
            self.login()
            response = self.session.get(
                url,
                params={
                    "onlyBlocked": "true",
                    "withinHours": 0
                },
                timeout=15
            )

        response.raise_for_status()

        data = response.json()

        if isinstance(data, dict):
            return data.get("data", [])

        return data

    def set_client_blocked(self, mac, blocked):
        url = (
            f"https://{self.host}"
            "/proxy/network/api/s/default/cmd/stamgr"
        )

        payload = {
            "mac": mac,
            "cmd": "block-sta" if blocked else "unblock-sta"
        }

        response = self.session.post(
            url,
            json=payload,
            timeout=15
        )

        if response.status_code in (401, 403):
            self.login()
            response = self.session.post(
                url,
                json=payload,
                timeout=15
            )

        response.raise_for_status()
        return response.json()

    def get_devices(self):
        url = (
            f"https://{self.host}"
            "/proxy/network/api/s/default/stat/device"
        )

        response = self.session.get(url, timeout=15)

        if response.status_code in (401, 403):
            self.login()
            response = self.session.get(url, timeout=15)

        response.raise_for_status()

        data = response.json()
        return data.get("data", [])

    def get_firewall_policies(self):
        url = (
            f"https://{self.host}"
            "/proxy/network/v2/api/site/default/firewall-policies"
        )

        response = self.session.get(url, timeout=15)

        if response.status_code in (401, 403):
            self.login()
            response = self.session.get(url, timeout=15)

        response.raise_for_status()

        data = response.json()

        if isinstance(data, dict):
            return data.get("data", [])

        return data

    def set_firewall_policy_enabled(self, policy_id, enabled):
        url = (
            f"https://{self.host}"
            "/proxy/network/v2/api/site/default/firewall-policies/batch"
        )

        payload = [
            {
                "_id": policy_id,
                "enabled": bool(enabled)
            }
        ]

        response = self.session.put(
            url,
            json=payload,
            timeout=15
        )

        if response.status_code in (401, 403):
            self.login()
            response = self.session.put(
                url,
                json=payload,
                timeout=15
            )

        response.raise_for_status()
        return response.json()

    def set_port_poe_mode(self, switch_id, port_idx, poe_mode):
        devices = self.get_devices()

        switch = next(
            (
                device for device in devices
                if device.get("_id") == switch_id
            ),
            None
        )

        if not switch:
            raise RuntimeError(
                f"UniFi switch {switch_id} not found"
            )

        overrides = [
            dict(item)
            for item in switch.get("port_overrides", [])
        ]

        target = next(
            (
                item for item in overrides
                if item.get("port_idx") == port_idx
            ),
            None
        )

        if not target:
            target = {
                "port_idx": port_idx,
                "poe_mode": poe_mode
            }
            overrides.append(target)
        else:
            target["poe_mode"] = poe_mode

        url = (
            f"https://{self.host}"
            f"/proxy/network/api/s/default/rest/device/{switch_id}"
        )

        response = self.session.put(
            url,
            json={"port_overrides": overrides},
            timeout=15
        )

        if response.status_code in (401, 403):
            self.login()
            response = self.session.put(
                url,
                json={"port_overrides": overrides},
                timeout=15
            )

        response.raise_for_status()
        return response.json()

    def get_wlans(self):
        url = (
            f"https://{self.host}"
            "/proxy/network/api/s/default/rest/wlanconf"
        )

        response = self.session.get(url, timeout=15)

        if response.status_code in (401, 403):
            self.login()
            response = self.session.get(url, timeout=15)

        response.raise_for_status()

        data = response.json()
        return data.get("data", [])

    def set_wlan_enabled(self, wlan_id, enabled):
        url = (
            f"https://{self.host}"
            f"/proxy/network/api/s/default/rest/wlanconf/{wlan_id}"
        )

        response = self.session.get(url, timeout=15)

        if response.status_code in (401, 403):
            self.login()
            response = self.session.get(url, timeout=15)

        response.raise_for_status()

        data = response.json().get("data", [])

        if not data:
            raise RuntimeError(f"UniFi WLAN {wlan_id} not found")

        wlan = dict(data[0])
        wlan["enabled"] = bool(enabled)

        # These are returned by UniFi but should not be sent back
        # as editable WLAN configuration fields.
        for key in ("_id", "site_id", "external_id"):
            wlan.pop(key, None)

        response = self.session.put(
            url,
            json=wlan,
            timeout=15
        )

        if response.status_code in (401, 403):
            self.login()
            response = self.session.put(
                url,
                json=wlan,
                timeout=15
            )

        response.raise_for_status()
        return response.json()

    def get_client_name(self, mac):
        end = int(time.time() * 1000)
        start = end - (24 * 60 * 60 * 1000)

        url = (
            f"https://{self.host}"
            f"/proxy/network/v2/api/site/default/traffic/{mac}"
        )

        params = {
            "start": start,
            "end": end,
            "includeUnidentified": "true",
            "mac": mac
        }

        response = self.session.get(
            url,
            params=params,
            timeout=15
        )

        if response.status_code in (401, 403):
            self.login()
            response = self.session.get(
                url,
                params=params,
                timeout=15
            )

        response.raise_for_status()
        data = response.json()

        def find_name(obj):
            if isinstance(obj, dict):
                if (
                    obj.get("mac", "").lower() == mac.lower()
                    and obj.get("name")
                ):
                    return obj.get("name")

                for value in obj.values():
                    result = find_name(value)
                    if result:
                        return result

            elif isinstance(obj, list):
                for value in obj:
                    result = find_name(value)
                    if result:
                        return result

            return None

        name = find_name(data)

        if name:
            # IoX rejects node names containing double quotes.
            name = name.replace('"', '')
            return name.strip()

        return None

    def set_enabled(self, route_id, enabled):
        routes = self.get_routes()

        route = next(
            (r for r in routes if r.get("_id") == route_id),
            None
        )

        if route is None:
            raise RuntimeError(f"Traffic route {route_id} not found")

        updated = dict(route)
        updated["enabled"] = bool(enabled)

        response = self.session.put(
            f"{self.base}/{route_id}",
            json=updated,
            timeout=15
        )

        if response.status_code in (401, 403):
            self.login()
            response = self.session.put(
                f"{self.base}/{route_id}",
                json=updated,
                timeout=15
            )

        response.raise_for_status()
        return response.json()


class TrafficRouteNode(udi_interface.Node):

    id = "unifiroute"

    drivers = [
        {"driver": "ST", "value": 0, "uom": 2}
    ]

    def __init__(self, polyglot, primary, address, name,
                 client, route_id):

        super().__init__(polyglot, address, address, name)

        self.client = client
        self.route_id = route_id

    def update_status(self, enabled):
        self.setDriver("ST", 1 if enabled else 0)

    def cmd_on(self, command):
        LOGGER.info("Enabling UniFi traffic route: %s", self.name)

        result = self.client.set_enabled(
            self.route_id,
            True
        )

        self.update_status(result.get("enabled", True))

    def cmd_off(self, command):
        LOGGER.info("Disabling UniFi traffic route: %s", self.name)

        result = self.client.set_enabled(
            self.route_id,
            False
        )

        self.update_status(result.get("enabled", False))

    def cmd_query(self, command):
        routes = self.client.get_routes()

        for route in routes:
            if route.get("_id") == self.route_id:
                self.update_status(route.get("enabled", False))
                return

    commands = {
        "DON": cmd_on,
        "DOF": cmd_off,
        "QUERY": cmd_query
    }


class UniFiSSIDNode(udi_interface.Node):

    id = "unifissid"

    drivers = [
        {"driver": "ST", "value": 0, "uom": 2}
    ]

    def __init__(
        self,
        polyglot,
        primary,
        address,
        name,
        client,
        wlan_id
    ):
        super().__init__(polyglot, address, address, name)

        self.client = client
        self.wlan_id = wlan_id

    def update_status(self, enabled):
        self.setDriver("ST", 1 if enabled else 0)

    def _refresh(self, delay=2):
        try:
            if delay:
                time.sleep(delay)

            wlans = self.client.get_wlans()

            for wlan in wlans:
                if wlan.get("_id") == self.wlan_id:
                    self.update_status(
                        wlan.get("enabled", False)
                    )
                    return

            LOGGER.warning(
                "SSID not found during refresh: %s",
                self.name
            )

        except Exception:
            LOGGER.exception(
                "SSID refresh failed: %s",
                self.name
            )

    def _schedule_refresh(self):
        threading.Thread(
            target=self._refresh,
            daemon=True
        ).start()

    def cmd_on(self, command):
        LOGGER.info(
            "Enabling UniFi SSID: %s",
            self.name
        )

        self.client.set_wlan_enabled(
            self.wlan_id,
            True
        )

        self._schedule_refresh()

    def cmd_off(self, command):
        LOGGER.info(
            "Disabling UniFi SSID: %s",
            self.name
        )

        self.client.set_wlan_enabled(
            self.wlan_id,
            False
        )

        self._schedule_refresh()

    def cmd_query(self, command):
        self._refresh(delay=0)

    commands = {
        "DON": cmd_on,
        "DOF": cmd_off,
        "QUERY": cmd_query
    }


class UniFiClientNode(udi_interface.Node):

    id = "unificlient"

    drivers = [
        {"driver": "ST", "value": 0, "uom": 2},
        {"driver": "GV1", "value": 0, "uom": 2}
    ]

    def __init__(
        self,
        polyglot,
        primary,
        address,
        name,
        mac,
        client
    ):
        super().__init__(polyglot, address, address, name)

        self.mac = mac.lower()
        self.client = client

    def update_status(self, online):
        self.setDriver("GV1", 1 if online else 0)

    def update_blocked(self, blocked):
        self.setDriver("ST", 1 if blocked else 0)

    def _refresh_blocked(self, delay=3):
        try:
            if delay:
                time.sleep(delay)

            blocked_clients = self.client.get_blocked_clients()

            blocked_macs = {
                item.get("mac", "").lower()
                for item in blocked_clients
                if item.get("mac")
            }

            self.update_blocked(
                self.mac in blocked_macs
            )

        except Exception:
            LOGGER.exception(
                "Client blocked-state refresh failed: %s",
                self.name
            )

    def _schedule_blocked_refresh(self):
        threading.Thread(
            target=self._refresh_blocked,
            daemon=True
        ).start()

    def cmd_block(self, command):
        LOGGER.info(
            "Blocking UniFi client: %s",
            self.name
        )

        self.client.set_client_blocked(
            self.mac,
            True
        )

        self._schedule_blocked_refresh()

    def cmd_unblock(self, command):
        LOGGER.info(
            "Unblocking UniFi client: %s",
            self.name
        )

        self.client.set_client_blocked(
            self.mac,
            False
        )

        self._schedule_blocked_refresh()

    def cmd_query(self, command):
        self._refresh_blocked(delay=0)

    commands = {
        "DON": cmd_block,
        "DOF": cmd_unblock,
        "BLOCK": cmd_block,
        "UNBLOCK": cmd_unblock,
        "QUERY": cmd_query
    }


class UniFiFirewallPolicyNode(udi_interface.Node):

    id = "unififirewall"

    drivers = [
        {"driver": "ST", "value": 0, "uom": 2}
    ]

    def __init__(
        self,
        polyglot,
        primary,
        address,
        name,
        client,
        policy_id
    ):
        super().__init__(polyglot, address, address, name)

        self.client = client
        self.policy_id = policy_id

    def update_status(self, enabled):
        self.setDriver("ST", 1 if enabled else 0)

    def _verified_refresh(self):
        try:
            time.sleep(3)

            policies = self.client.get_firewall_policies()

            for policy in policies:
                if policy.get("_id") == self.policy_id:
                    self.update_status(
                        policy.get("enabled", False)
                    )
                    return

            LOGGER.warning(
                "Firewall policy not found during refresh: %s",
                self.name
            )

        except Exception:
            LOGGER.exception(
                "Firewall policy refresh failed: %s",
                self.name
            )

    def _schedule_refresh(self):
        threading.Thread(
            target=self._verified_refresh,
            daemon=True
        ).start()

    def cmd_on(self, command):
        LOGGER.info(
            "Enabling UniFi firewall policy: %s",
            self.name
        )

        self.client.set_firewall_policy_enabled(
            self.policy_id,
            True
        )

        self._schedule_refresh()

    def cmd_off(self, command):
        LOGGER.info(
            "Disabling UniFi firewall policy: %s",
            self.name
        )

        self.client.set_firewall_policy_enabled(
            self.policy_id,
            False
        )

        self._schedule_refresh()

    def cmd_query(self, command):
        policies = self.client.get_firewall_policies()

        for policy in policies:
            if policy.get("_id") == self.policy_id:
                self.update_status(
                    policy.get("enabled", False)
                )
                return

    commands = {
        "DON": cmd_on,
        "DOF": cmd_off,
        "QUERY": cmd_query
    }


class UniFiSwitchNode(udi_interface.Node):

    id = "unifiswitch"

    drivers = [
        {"driver": "ST", "value": 0, "uom": 2},
    ]

    def __init__(
        self,
        polyglot,
        primary,
        address,
        name,
        switch_id,
        switch_mac
    ):
        # Physical switch nodes are their own primary. This is intentional:
        # the switch is a real IoX node that acts as the parent for its ports.
        # Other top-level UniFi nodes likewise use their own address as primary
        # so they appear directly beneath the main UniFi Control node.
        super().__init__(polyglot, address, address, name)

        self.switch_id = switch_id
        self.switch_mac = switch_mac.lower()

    def update_status(self, switch):
        self.setDriver(
            "ST",
            1 if switch.get("state") == 1 else 0
        )


class UniFiPortNode(udi_interface.Node):

    id = "unifiport"

    drivers = [
        {"driver": "ST",  "value": 0, "uom": 2},
        {"driver": "GV1", "value": 0, "uom": 56},
    ]

    def __init__(
        self,
        polyglot,
        primary,
        address,
        name,
        switch_id,
        switch_mac,
        port_idx
    ):
        super().__init__(polyglot, primary, address, name)

        self.switch_id = switch_id
        self.switch_mac = switch_mac.lower()
        self.port_idx = port_idx

    def update_status(self, port):
        self.setDriver("ST", 1 if port.get("up") else 0)
        self.setDriver("GV1", port.get("speed") or 0)


class UniFiPoePortNode(udi_interface.Node):

    id = "unifipoeport"

    drivers = [
        {"driver": "ST",  "value": 0, "uom": 2},
        {"driver": "GV1", "value": 0, "uom": 56},
        {"driver": "GV2", "value": 0, "uom": 2},
        {"driver": "GV3", "value": 0, "uom": 73},
    ]

    def __init__(
        self,
        polyglot,
        primary,
        address,
        name,
        client,
        switch_id,
        switch_mac,
        port_idx
    ):
        super().__init__(polyglot, primary, address, name)

        self.client = client
        self.switch_id = switch_id
        self.switch_mac = switch_mac.lower()
        self.port_idx = port_idx

    def update_status(self, port):
        self.setDriver("GV2", 1 if port.get("up") else 0)
        self.setDriver("GV1", port.get("speed") or 0)
        poe_mode = port.get("poe_mode")

        if poe_mode == "auto":
            poe_status = 1
        else:
            poe_status = 0

        self.setDriver("ST", poe_status)

        try:
            power = float(port.get("poe_power") or 0)
        except (TypeError, ValueError):
            power = 0

        self.setDriver("GV3", power)

    def _refresh_port(self, delay=2):
        """Read this port back from UniFi and update IoX."""
        try:
            if delay:
                time.sleep(delay)

            devices = self.client.get_devices()

            for switch in devices:
                if switch.get("_id") != self.switch_id:
                    continue

                for port in switch.get("port_table", []):
                    if port.get("port_idx") == self.port_idx:
                        self.update_status(port)
                        return

            LOGGER.warning(
                "Unable to refresh PoE port: %s port %s",
                self.name,
                self.port_idx
            )

        except Exception:
            LOGGER.exception(
                "PoE port refresh failed: %s port %s",
                self.name,
                self.port_idx
            )

    def _delayed_refresh(self):
        self._refresh_port(delay=2)

    def cmd_poe_on(self, command):
        LOGGER.info(
            "Enabling PoE: %s port %s",
            self.name,
            self.port_idx
        )

        self.client.set_port_poe_mode(
            self.switch_id,
            self.port_idx,
            "auto"
        )

        threading.Thread(
            target=self._delayed_refresh,
            daemon=True
        ).start()

    def cmd_poe_off(self, command):
        LOGGER.info(
            "Disabling PoE: %s port %s",
            self.name,
            self.port_idx
        )

        self.client.set_port_poe_mode(
            self.switch_id,
            self.port_idx,
            "off"
        )

        threading.Thread(
            target=self._delayed_refresh,
            daemon=True
        ).start()

    def _poe_cycle(self):
        try:
            LOGGER.info(
                "Cycling PoE: %s port %s",
                self.name,
                self.port_idx
            )

            self.client.set_port_poe_mode(
                self.switch_id,
                self.port_idx,
                "off"
            )

            # Verify the actual Off state from UniFi.
            self._refresh_port(delay=2)

            # Keep PoE off for approximately five seconds total.
            time.sleep(3)

            self.client.set_port_poe_mode(
                self.switch_id,
                self.port_idx,
                "auto"
            )

            # Verify the actual restored state from UniFi.
            self._refresh_port(delay=2)

        except Exception:
            LOGGER.exception(
                "PoE cycle failed: %s port %s",
                self.name,
                self.port_idx
            )

    def cmd_poe_cycle(self, command):
        threading.Thread(
            target=self._poe_cycle,
            daemon=True
        ).start()

    commands = {
        "DON": cmd_poe_on,
        "DOF": cmd_poe_off,
        "POEON": cmd_poe_on,
        "POEOFF": cmd_poe_off,
        "POECYCLE": cmd_poe_cycle
    }


class Controller(udi_interface.Node):

    id = "controller"

    drivers = [
        {"driver": "ST", "value": 0, "uom": 2}
    ]

    def __init__(self, polyglot):
        super().__init__(
            polyglot,
            "controller",
            "controller",
            "UniFi Control"
        )

        self.poly = polyglot
        self.client = None
        self.route_nodes = {}
        self.client_nodes = {}
        self.client_group_name = "IoX"
        self.switch_nodes = {}
        self.port_nodes = {}
        self.firewall_nodes = {}
        self.ssid_nodes = {}
        self.n_queue = []

    # poly.addNode() is asynchronous. IoX sends ADDNODEDONE when the node
    # has actually been created (or when creation fails). We retain the
    # complete response because an address alone cannot distinguish success
    # from an error such as HTTP 400.
    def node_queue(self, data):
        LOGGER.debug("ADDNODEDONE data: %r", data)
        address = data.get("address")
        if address:
            self.n_queue.append(data)

    def wait_for_node_done(self, address, timeout=30):
        deadline = time.time() + timeout

        while time.time() < deadline:
            for data in list(self.n_queue):
                if data.get("address") == address:
                    self.n_queue.remove(data)

                    if data.get("error"):
                        LOGGER.error(
                            "Failed to add node %s: %s",
                            address,
                            data.get("error")
                        )
                        return False

                    return True

            time.sleep(0.1)

        LOGGER.error(
            "Timed out waiting for ADDNODEDONE for %s",
            address
        )
        return False

    def configure(self, params):
        host = params.get("host")
        username = params.get("username")
        password = params.get("password")

        if not host or not username or not password:
            LOGGER.warning(
                "Please configure host, username and password in PG3x."
            )
            self.setDriver("ST", 0)
            return

        try:
            LOGGER.info("Configuring UniFi connection")

            self.client = UniFiClient(
                host,
                username,
                password
            )

            self.client.login()
            self.discover()

            self.setDriver("ST", 1)

        except Exception:
            LOGGER.exception("Unable to initialize UniFi")

            # Do not continuously retry failed authentication on every poll.
            # A new CUSTOMPARAMS event or plugin restart will try again.
            self.client = None

            self.setDriver("ST", 0)

    def discover(self):
        routes = self.client.get_routes()

        LOGGER.info(
            "Discovered %d UniFi traffic route(s)",
            len(routes)
        )

        for route in routes:
            route_id = route.get("_id")
            name = route.get("description") or route_id

            address = "ur" + route_id[-12:]

            if address not in self.route_nodes:
                node = TrafficRouteNode(
                    self.poly,
                    self.address,
                    address,
                    name,
                    self.client,
                    route_id
                )

                self.poly.addNode(node)
                self.route_nodes[address] = node

            self.route_nodes[address].update_status(
                route.get("enabled", False)
            )

        groups = self.client.get_client_groups()

        group = next(
            (
                g for g in groups
                if g.get("name") == self.client_group_name
                and g.get("type") == "CLIENTS"
            ),
            None
        )

        if group is None:
            LOGGER.info(
                "UniFi client group '%s' not found",
                self.client_group_name
            )
            return

        member_macs = {
            mac.lower()
            for mac in group.get("members", [])
        }

        LOGGER.info(
            "UniFi client group '%s' contains %d client(s)",
            self.client_group_name,
            len(member_macs)
        )

        clients = self.client.get_clients()

        clients_by_mac = {
            c.get("mac", "").lower(): c
            for c in clients
            if c.get("mac")
        }

        for mac in member_macs:
            client = clients_by_mac.get(mac)

            online = client is not None

            address = "uc" + mac.replace(":", "")

            if address not in self.client_nodes:
                try:
                    name = self.client.get_client_name(mac) or mac
                except Exception:
                    LOGGER.exception(
                        "Unable to retrieve UniFi name for client %s",
                        mac
                    )
                    name = mac

                node = UniFiClientNode(
                    self.poly,
                    self.address,
                    address,
                    name,
                    mac,
                    self.client
                )

                self.poly.addNode(node)
                self.client_nodes[address] = node

            self.client_nodes[address].update_status(online)

        # Discover user-created UniFi firewall policies.
        policies = self.client.get_firewall_policies()

        user_policies = [
            policy for policy in policies
            if policy.get("predefined") is False
        ]

        LOGGER.info(
            "Discovered %d user-created UniFi firewall policy/policies",
            len(user_policies)
        )

        for policy in user_policies:
            policy_id = policy.get("_id")
            policy_name = policy.get("name")

            if not policy_id or not policy_name:
                continue

            # IoX addresses must be short and stable.
            address = "uf" + policy_id[-12:]

            if address not in self.firewall_nodes:
                # IoX rejects node names containing double quotes.
                name = policy_name.replace('"', '').strip()

                node = UniFiFirewallPolicyNode(
                    self.poly,
                    self.address,
                    address,
                    name,
                    self.client,
                    policy_id
                )

                self.poly.addNode(node)
                self.firewall_nodes[address] = node

            self.firewall_nodes[address].update_status(
                policy.get("enabled", False)
            )

        # Discover UniFi SSIDs.
        wlans = self.client.get_wlans()

        LOGGER.info(
            "Discovered %d UniFi SSID(s)",
            len(wlans)
        )

        for wlan in wlans:
            wlan_id = wlan.get("_id")
            wlan_name = wlan.get("name")

            if not wlan_id or not wlan_name:
                continue

            # Stable, short IoX address based on the UniFi WLAN ID.
            address = "uw" + wlan_id[-12:]

            if address not in self.ssid_nodes:
                name = wlan_name.replace('"', '').strip()

                node = UniFiSSIDNode(
                    self.poly,
                    self.address,
                    address,
                    name,
                    self.client,
                    wlan_id
                )

                self.poly.addNode(node)
                self.ssid_nodes[address] = node

            self.ssid_nodes[address].update_status(
                wlan.get("enabled", False)
            )

        # Discover UniFi switch ports.
        devices = self.client.get_devices()

        switches = [
            device for device in devices
            if device.get("type") == "usw"
        ]

        LOGGER.info(
            "Discovered %d UniFi switch(es)",
            len(switches)
        )

        for switch in switches:
            switch_id = switch.get("_id")
            switch_mac = switch.get("mac", "")
            switch_name = (
                switch.get("name")
                or switch.get("model")
                or switch_mac
                or "UniFi Switch"
            )

            # Shorten common UniFi model prefixes for IoX display.
            for prefix in ("US 8 60W ", "USW Flex Mini "):
                if switch_name.startswith(prefix):
                    switch_name = switch_name[len(prefix):]
                    break

            if not switch_id or not switch_mac:
                continue

            # Create one IoX node for the physical switch. The switch is
            # self-primary and therefore appears directly under UniFi Control.
            # Ports use this switch node as their primary node.
            switch_address = (
                "us"
                + switch_mac.replace(":", "")[-12:]
            )

            if switch_address not in self.switch_nodes:
                node = UniFiSwitchNode(
                    self.poly,
                    self.address,
                    switch_address,
                    switch_name,
                    switch_id,
                    switch_mac
                )

                # Do not create the child ports until IoX confirms that the
                # switch node exists. Creating parent and children immediately
                # can race IoX's asynchronous node creation and produce HTTP
                # 400 errors for otherwise valid port nodes.
                self.poly.addNode(node)
                if not self.wait_for_node_done(switch_address):
                    LOGGER.error(
                        "Skipping ports for switch %s because the switch node was not added",
                        switch_address
                    )
                    continue
                self.switch_nodes[switch_address] = node

            self.switch_nodes[switch_address].update_status(switch)

            for port in switch.get("port_table", []):
                port_idx = port.get("port_idx")

                if port_idx is None:
                    continue

                port_name = (
                    port.get("name")
                    or f"Port {port_idx}"
                )

                name = f"{port_name} - {switch_name}"

                # Stable IoX address based on switch MAC and physical port.
                address = (
                    "up"
                    + switch_mac.replace(":", "")[-10:]
                    + f"{int(port_idx):02d}"
                )

                if address not in self.port_nodes:
                    if port.get("port_poe"):
                        node = UniFiPoePortNode(
                            self.poly,
                            switch_address,
                            address,
                            name,
                            self.client,
                            switch_id,
                            switch_mac,
                            port_idx
                        )
                    else:
                        node = UniFiPortNode(
                            self.poly,
                            switch_address,
                            address,
                            name,
                            switch_id,
                            switch_mac,
                            port_idx
                        )

                    # Only remember the port after IoX confirms creation.
                    # Failed additions are deliberately left out so discovery
                    # can retry them on a later pass.
                    self.poly.addNode(node)
                    if not self.wait_for_node_done(address):
                        LOGGER.error(
                            "Port node %s was not added; it will be retried on next discovery",
                            address
                        )
                        continue
                    self.port_nodes[address] = node

                self.port_nodes[address].update_status(port)

    def update_ports(self):
        try:
            devices = self.client.get_devices()

            for switch in devices:
                if switch.get("type") != "usw":
                    continue

                switch_mac = switch.get("mac", "")
                if not switch_mac:
                    continue

                for port in switch.get("port_table", []):
                    port_idx = port.get("port_idx")
                    if port_idx is None:
                        continue

                    address = (
                        "up"
                        + switch_mac.replace(":", "")[-10:]
                        + f"{int(port_idx):02d}"
                    )

                    node = self.port_nodes.get(address)
                    if node:
                        node.update_status(port)

        except Exception:
            LOGGER.exception("Error updating UniFi switch ports")

    def poll(self, polltype):
        if not self.client:
            return

        if polltype == "longPoll":
            try:
                self.discover()
                self.setDriver("ST", 1)
            except Exception:
                LOGGER.exception("UniFi discovery poll failed")
                self.setDriver("ST", 0)
            return

        if polltype != "shortPoll":
            return

        try:
            routes = self.client.get_routes()

            by_id = {
                route.get("_id"): route
                for route in routes
            }

            for node in self.route_nodes.values():
                route = by_id.get(node.route_id)

                if route:
                    node.update_status(
                        route.get("enabled", False)
                    )

            clients = self.client.get_clients()

            online_macs = {
                c.get("mac", "").lower()
                for c in clients
                if c.get("mac")
            }

            blocked_clients = self.client.get_blocked_clients()

            blocked_macs = {
                c.get("mac", "").lower()
                for c in blocked_clients
                if c.get("mac")
            }

            for node in self.client_nodes.values():
                node.update_status(
                    node.mac in online_macs
                )
                node.update_blocked(
                    node.mac in blocked_macs
                )

            policies = self.client.get_firewall_policies()

            firewall_by_id = {
                policy.get("_id"): policy
                for policy in policies
                if policy.get("predefined") is False
            }

            for node in self.firewall_nodes.values():
                policy = firewall_by_id.get(node.policy_id)

                if policy:
                    node.update_status(
                        policy.get("enabled", False)
                    )

            wlans = self.client.get_wlans()

            wlan_by_id = {
                wlan.get("_id"): wlan
                for wlan in wlans
                if wlan.get("_id")
            }

            for node in self.ssid_nodes.values():
                wlan = wlan_by_id.get(node.wlan_id)

                if wlan:
                    node.update_status(
                        wlan.get("enabled", False)
                    )

            self.update_ports()

            self.setDriver("ST", 1)

        except Exception:
            LOGGER.exception("UniFi polling failed")
            self.setDriver("ST", 0)

    def cmd_query(self, command):
        if self.client:
            self.discover()

    commands = {
        "QUERY": cmd_query
    }


controller = None


def controller_node_queue(data):
    if controller is not None:
        controller.node_queue(data)


def custom_params_handler(params):
    global controller

    LOGGER.info("Received custom parameters")

    if controller is None:
        controller = Controller(polyglot)
        polyglot.addNode(controller)

    controller.configure(params)


def poll_handler(poll_type):
    if controller is None:
        return

    controller.poll(poll_type)


if __name__ == "__main__":

    polyglot = udi_interface.Interface([])

    try:
        polyglot.start("1.1.3")

        polyglot.subscribe(
            polyglot.ADDNODEDONE,
            controller_node_queue
        )

        polyglot.subscribe(
            polyglot.CUSTOMPARAMS,
            custom_params_handler
        )

        polyglot.subscribe(
            polyglot.POLL,
            poll_handler
        )

        polyglot.ready()
        polyglot.updateProfile()
        polyglot.runForever()

    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)

    except Exception:
        LOGGER.exception("Unhandled exception")
        polyglot.stop()
        sys.exit(1)
