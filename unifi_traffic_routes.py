#!/usr/bin/env python3

import sys
import time
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

        super().__init__(polyglot, primary, address, name)

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
            "UniFi Traffic Routes"
        )

        self.poly = polyglot
        self.client = None
        self.route_nodes = {}

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

    def poll(self, polltype):
        if polltype != "shortPoll":
            return

        if not self.client:
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
        polyglot.start("1.0.0")

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
