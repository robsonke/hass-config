"""
SamsungTVWS - Samsung Smart TV WS API wrapper

Copyright (C) 2019 Xchwarze
Copyright (C) 2020 Ollo69

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor,
    Boston, MA  02110-1335  USA

"""
import base64
from datetime import datetime
from enum import Enum
import json
import logging
import requests
import socket
import ssl
import subprocess
import sys
from threading import Thread, Lock
import time
from typing import Any
from urllib.parse import urlencode, urljoin
import uuid
import websocket

from . import shortcuts

DEFAULT_POWER_ON_DELAY = 120
MIN_APP_SCAN_INTERVAL = 10
MAX_WS_PING_INTERVAL = 10
PING_TIMEOUT = 3
TYPE_DEEP_LINK = "DEEP_LINK"
TYPE_NATIVE_LAUNCH = "NATIVE_LAUNCH"

_WS_ENDPOINT_REMOTE_CONTROL = "/api/v2/channels/samsung.remote.control"
_WS_ENDPOINT_APP_CONTROL = "/api/v2"
_WS_ENDPOINT_ART = "/api/v2/channels/com.samsung.art-app"

_LOGGING = logging.getLogger(__name__)


def _format_rest_url(host: str, append: str = "") -> str:
    """Return URL used for rest commands."""
    return f"http://{host}:8001/api/v2/{append}"


def gen_uuid():
    """Generate new uuid."""
    return str(uuid.uuid4())


def kill_subprocess(
    process: subprocess.Popen[Any],
) -> None:
    """Force kill a subprocess and wait for it to exit."""
    process.kill()
    process.communicate()
    process.wait()

    del process


class Ping:
    """Class for handling Ping to a specific host."""

    def __init__(self, host):
        """Initialize the object."""
        self._ip_address = host
        if sys.platform == "win32":
            self._ping_cmd = ["ping", "-n", "1", "-w", "2000", host]
        else:
            self._ping_cmd = ["ping", "-n", "-q", "-c1", "-W2", host]

    def ping(self, port=0):
        """Check if IP is available using ICMP or trying open a specific port."""
        if port > 0:
            return self._ping_socket(port)
        return self._ping()

    def _ping(self):
        """Send ICMP echo request and return True if success."""
        with subprocess.Popen(
                self._ping_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        ) as pinger:
            try:
                pinger.communicate(timeout=1+PING_TIMEOUT)
                return pinger.returncode == 0
            except subprocess.TimeoutExpired:
                kill_subprocess(pinger)
                return False
            except subprocess.CalledProcessError:
                return False

    def _ping_socket(self, port):
        """Check if port is available and return True if success."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(PING_TIMEOUT-1)
            return s.connect_ex((self._ip_address, port)) == 0


class ConnectionFailure(Exception):
    """Error during connection."""
    pass


class ResponseError(Exception):
    """Error in response."""
    pass


class HttpApiError(Exception):
    """Error using HTTP API."""
    pass


class App:
    """Define a TV Application."""
    def __init__(self, app_id, app_name, app_type):
        self.app_id = app_id
        self.app_name = app_name
        self.app_type = app_type


class ArtModeStatus(Enum):
    """Define possible ArtMode status."""
    Unsupported = 0
    Unavailable = 1
    Off = 2
    On = 3


class SamsungTVWS:
    """Class to manage websocket communication with tizen TV."""

    def __init__(
        self,
        host,
        token=None,
        token_file=None,
        port=8001,
        timeout=None,
        key_press_delay=1.0,
        name="SamsungTvRemote",
        app_list=None,
    ):
        """Initialize SamsungTVWS object."""
        self.host = host
        self.token = token
        self.token_file = token_file
        self.port = port or 8001
        self.timeout = None if timeout == 0 else timeout
        self.key_press_delay = key_press_delay
        self.name = name or "SamsungTvRemote"
        self.connection = None
        self._app_list = app_list
        self._artmode_status = ArtModeStatus.Unsupported
        self._power_on_requested = False
        self._power_on_requested_time = datetime.min
        self._power_on_delay = DEFAULT_POWER_ON_DELAY
        self._power_on_artmode = False

        self._installed_app = {}
        self._running_app = None
        self._app_type = {}
        self._sync_lock = Lock()
        self._last_app_scan = datetime.min
        self._is_connected = False

        self._ws_remote = None
        self._client_remote = None
        self._last_ping = datetime.min

        self._ws_control = None
        self._client_control = None
        self._last_control_ping = datetime.min

        self._ws_art = None
        self._client_art = None
        self._last_art_ping = datetime.min
        self._client_art_supported = 2

        self._ping = Ping(self.host)
        self._new_token_callback = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    @staticmethod
    def ping_probe(host):
        """Try to ping device and return usable port."""
        ping = Ping(host)
        for port in (9197, 0):
            try:
                if ping.ping(port):
                    return port
            except Exception:
                _LOGGING.debug("Failed to ping device using port %s", port)

        return None

    @staticmethod
    def _serialize_string(string):
        if isinstance(string, str):
            string = str.encode(string)
        return base64.b64encode(string).decode("utf-8")

    def _is_ssl_connection(self):
        return self.port == 8002

    def _format_websocket_url(self, path, is_ssl=False, use_token=True):
        scheme = "wss" if is_ssl else "ws"

        base_uri = f"{scheme}://{self.host}:{self.port}"
        ws_uri = urljoin(base_uri, path)
        query = {"name": self._serialize_string(self.name)}
        if is_ssl and use_token:
            if token := self._get_token():
                query["token"] = token
        ws_query = urlencode(query)
        return f"{ws_uri}?{ws_query}"

    def register_new_token_callback(self, func):
        """Register a callback function."""
        self._new_token_callback = func

    def _get_token(self):
        """Get current token."""
        if self.token_file is not None:
            try:
                with open(self.token_file, "r") as token_file:
                    return token_file.readline()
            except Exception as exc:
                _LOGGING.error("Failed to read TV token file: %s", str(exc))
                return ""
        return self.token

    def _set_token(self, token):
        """Save new token."""
        _LOGGING.debug("New token %s", token)
        if self.token_file is not None:
            _LOGGING.debug("Save new token to file %s", self.token_file)
            with open(self.token_file, "w") as token_file:
                token_file.write(token)
            return

        if self.token is not None and self.token == token:
            return
        self.token = token
        if self._new_token_callback is not None:
            self._new_token_callback()

    def _ws_send(self, command, key_press_delay=None, *, use_control=False, ws_socket=None):
        using_remote = False
        if not use_control:
            if self._ws_remote:
                connection = self._ws_remote
                using_remote = True
            else:
                connection = self.open()
        elif ws_socket:
            connection = ws_socket
        else:
            self.start_client(start_all=True)
            return False

        payload = json.dumps(command)
        try:
            connection.send(payload)
        except websocket.WebSocketConnectionClosedException:
            _LOGGING.warning("_ws_send: connection is closed, send command failed")
            if using_remote or use_control:
                _LOGGING.info("_ws_send: try to restart communication threads")
                self.start_client(start_all=use_control)
            return False
        except websocket.WebSocketTimeoutException:
            _LOGGING.warning("_ws_send: timeout error sending command %s", payload)
            return False

        if using_remote:
            # we consider a message sent valid as a ping
            self._last_ping = datetime.utcnow()

        if key_press_delay is None:
            if self.key_press_delay > 0:
                time.sleep(self.key_press_delay)
        elif key_press_delay > 0:
            time.sleep(key_press_delay)

        return True

    def _rest_request(self, target, method="GET"):
        url = _format_rest_url(self.host, target)
        try:
            if method == "POST":
                return requests.post(url, timeout=self.timeout)
            elif method == "PUT":
                return requests.put(url, timeout=self.timeout)
            elif method == "DELETE":
                return requests.delete(url, timeout=self.timeout)
            else:
                return requests.get(url, timeout=self.timeout)
        except requests.ConnectionError:
            raise HttpApiError(
                "TV unreachable or feature not supported on this model."
            )

    @staticmethod
    def _process_api_response(response, *, raise_error=True):
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            _LOGGING.debug(
                "Failed to parse response from TV. response text: %s", response
            )
            if raise_error:
                raise ResponseError(
                    "Failed to parse response from TV. Maybe feature not supported on this model"
                )
        return response

    def _check_conn_id(self, resp_data):
        if not resp_data:
            return False

        msg_id = resp_data.get("id")
        if not msg_id:
            return False

        clients_info = resp_data.get("clients")
        for client in clients_info:
            device_name = client.get("deviceName")
            if device_name:
                if device_name == self._serialize_string(self.name):
                    conn_id = client.get("id", "")
                    if conn_id == msg_id:
                        return True
        return False

    def _client_remote_thread(self):
        if self._ws_remote:
            return

        is_ssl = self._is_ssl_connection()
        url = self._format_websocket_url(
            _WS_ENDPOINT_REMOTE_CONTROL,
            is_ssl=is_ssl
        )
        sslopt = {"cert_reqs": ssl.CERT_NONE} if is_ssl else {}

        websocket.setdefaulttimeout(self.timeout)
        self._ws_remote = websocket.WebSocketApp(
            url,
            on_message=self._on_message_remote,
            on_ping=self._on_ping_remote,
        )
        _LOGGING.debug("Thread SamsungRemote started")
        # we set ping interval (1 hour) only to enable multi-threading mode
        # on socket. TV do not answer to ping but send ping to client
        self._ws_remote.run_forever(
            sslopt=sslopt, ping_interval=3600
        )
        self._is_connected = False
        if self._ws_art:
            self._ws_art.close()
        if self._ws_control:
            self._ws_control.close()
        self._ws_remote.close()
        self._ws_remote = None
        _LOGGING.debug("Thread SamsungRemote terminated")

    def _on_ping_remote(self, _, payload):
        _LOGGING.debug("Received WS remote ping %s, sending pong", payload)
        self._last_ping = datetime.utcnow()
        if self._ws_remote.sock:
            try:
                self._ws_remote.sock.pong(payload)
            except Exception as ex:
                _LOGGING.warning("WS remote send_pong failed, %s", ex)

    def _on_message_remote(self, _, message):
        response = self._process_api_response(message)
        _LOGGING.debug(response)
        event = response.get("event")
        if not event:
            return

        # we consider a message valid as a ping
        self._last_ping = datetime.utcnow()

        if event == "ms.channel.connect":
            conn_data = response.get("data")
            if not self._check_conn_id(conn_data):
                return
            _LOGGING.debug("Message remote: received connect")
            token = conn_data.get("token")
            if token:
                self._set_token(token)
            self._is_connected = True
            self._request_apps_list()
            self.start_client(start_all=True)
        elif event == "ed.installedApp.get":
            _LOGGING.debug("Message remote: received installedApp")
            self._handle_installed_app(response)
        elif event == "ed.edenTV.update":
            _LOGGING.debug("Message remote: received edenTV")
            self.get_running_app(force_scan=True)

    def _request_apps_list(self):
        _LOGGING.debug("Request app list")
        self._ws_send(
            {
                "method": "ms.channel.emit",
                "params": {"event": "ed.installedApp.get", "to": "host"},
            },
            key_press_delay=0,
        )

    def _handle_installed_app(self, response):
        list_app = response.get("data", {}).get("data")
        installed_app = {}
        for app_info in list_app:
            app_id = app_info["appId"]
            _LOGGING.debug("Found app: %s", app_id)
            app = App(app_id, app_info["name"], app_info["app_type"])
            installed_app[app_id] = app
        self._installed_app = installed_app

    def _client_control_thread(self):
        if self._ws_control:
            return

        is_ssl = self._is_ssl_connection()
        url = self._format_websocket_url(
            _WS_ENDPOINT_APP_CONTROL,
            is_ssl=is_ssl,
            use_token=False
        )
        sslopt = {"cert_reqs": ssl.CERT_NONE} if is_ssl else {}

        websocket.setdefaulttimeout(self.timeout)
        self._ws_control = websocket.WebSocketApp(
            url,
            on_message=self._on_message_control,
            on_ping=self._on_ping_control,
        )
        _LOGGING.debug("Thread SamsungControl started")
        # we set ping interval (1 hour) only to enable multi-threading mode
        # on socket. TV do not answer to ping but send ping to client
        self._ws_control.run_forever(
            sslopt=sslopt, ping_interval=3600
        )
        self._ws_control.close()
        self._ws_control = None
        _LOGGING.debug("Thread SamsungControl terminated")

    def _on_ping_control(self, _, payload):
        _LOGGING.debug("Received WS control ping %s, sending pong", payload)
        self._last_control_ping = datetime.utcnow()
        if self._ws_control.sock:
            try:
                self._ws_control.sock.pong(payload)
            except Exception as ex:
                _LOGGING.warning("WS control send_pong failed, %s", ex)

    def _on_message_control(self, _, message):
        response = self._process_api_response(message)
        _LOGGING.debug(response)
        result = response.get("result")
        if result:
            self._set_running_app(response)
            return
        error = response.get("error")
        if error:
            self._manage_control_err(response)
            return
        event = response.get("event")
        if not event:
            return
        if event == "ms.channel.connect":
            conn_data = response.get("data")
            if not self._check_conn_id(conn_data):
                return
            _LOGGING.debug("Message control: received connect")
            self.get_running_app()
        elif event == "ed.installedApp.get":
            _LOGGING.debug("Message control: received installedApp")
            self._handle_installed_app(response)

    def _set_running_app(self, response):
        app_id = response.get("id")
        if not app_id:
            return
        result = response.get("result")
        if result is None:
            return
        elif isinstance(result, bool):
            is_running = result
        else:
            is_running = result.get("visible")
        if is_running is None:
            return

        if self._running_app:
            if is_running and app_id != self._running_app:
                _LOGGING.debug("app running: %s", app_id)
                self._running_app = app_id
            elif not is_running and app_id == self._running_app:
                _LOGGING.debug("app stopped: %s", app_id)
                self._running_app = None
        elif is_running:
            _LOGGING.debug("app running: %s", app_id)
            self._running_app = app_id

    def _manage_control_err(self, response):
        app_id = response.get("id")
        if not app_id:
            return
        error_code = response.get("error", {}).get("code", 0)
        if error_code == 404:  # Not found error
            if self._installed_app:
                if app_id not in self._installed_app:
                    _LOGGING.error("App ID %s not found", app_id)
                return
            # app_type = self._app_type.get(app_id)
            # if app_type is None:
            #     _LOGGING.info(
            #         "App ID %s with type DEEP_LINK not found, set as NATIVE_LAUNCH",
            #         app_id,
            #     )
            #     self._app_type[app_id] = 4

    def _get_app_status(self, app_id, app_type):
        _LOGGING.debug("Get app status: AppID: %s, AppType: %s", app_id, app_type)

        # if app_type == 4:
        #     method = "ms.webapplication.get"
        # else:
        #     method = "ms.application.get"

        if app_type == 4:  # app type 4 always return not found error
            return
        method = "ms.application.get"
        self._ws_send(
            {
                "id": app_id,
                "method": method,
                "params": {"id": app_id},
            },
            key_press_delay=0,
            use_control=True,
            ws_socket=self._ws_control,
        )

    def _client_art_thread(self):
        if self._ws_art:
            return

        is_ssl = self._is_ssl_connection()
        url = self._format_websocket_url(
            _WS_ENDPOINT_ART,
            is_ssl=is_ssl,
            use_token=False
        )
        sslopt = {"cert_reqs": ssl.CERT_NONE} if is_ssl else {}

        websocket.setdefaulttimeout(self.timeout)
        self._ws_art = websocket.WebSocketApp(
            url,
            on_message=self._on_message_art,
            on_ping=self._on_ping_art,
        )
        _LOGGING.debug("Thread SamsungArt started")
        # we set ping interval (1 hour) only to enable multi-threading mode
        # on socket. TV do not answer to ping but send ping to client
        self._ws_art.run_forever(
            sslopt=sslopt, ping_interval=3600
        )
        self._ws_art.close()
        self._ws_art = None
        _LOGGING.debug("Thread SamsungArt terminated")

    def _on_ping_art(self, _, payload):
        _LOGGING.debug("Received WS art ping %s, sending pong", payload)
        self._last_art_ping = datetime.utcnow()
        if self._ws_art.sock:
            try:
                self._ws_art.sock.pong(payload)
            except Exception as ex:
                _LOGGING.warning("WS art send_pong failed: %s", ex)

    def _on_message_art(self, _, message):
        response = self._process_api_response(message)
        _LOGGING.debug(response)
        event = response.get("event")
        if not event:
            return

        # we consider a message valid as a ping
        self._last_art_ping = datetime.utcnow()

        if event == "ms.channel.connect":
            conn_data = response.get("data")
            if not self._check_conn_id(conn_data):
                return
            _LOGGING.debug("Message art: received connect")
            self._client_art_supported = 1
        elif event == "ms.channel.ready":
            _LOGGING.debug("Message art: channel ready")
            self._get_artmode_status()
        elif event == "d2d_service_message":
            _LOGGING.debug("Message art: d2d message")
            self._handle_artmode_status(response)

    def _get_artmode_status(self):
        _LOGGING.debug("Sending get_art_status")
        msg_data = {
            "request": "get_artmode_status",
            "id": gen_uuid(),
        }
        self._ws_send(
            {
                "method": "ms.channel.emit",
                "params": {
                    "data": json.dumps(msg_data),
                    "to": "host",
                    "event": "art_app_request",
                },
            },
            key_press_delay=0,
            use_control=True,
            ws_socket=self._ws_art,
        )

    def _handle_artmode_status(self, response):
        data_str = response.get("data")
        if not data_str:
            return
        data = self._process_api_response(data_str)
        event = data.get("event", "")
        if event == "art_mode_changed":
            status = data.get("status", "")
            if status == "on":
                artmode_status = ArtModeStatus.On
            else:
                artmode_status = ArtModeStatus.Off
        elif event == "artmode_status":
            value = data.get("value", "")
            if value == "on":
                artmode_status = ArtModeStatus.On
            else:
                artmode_status = ArtModeStatus.Off
        elif event == "go_to_standby":
            artmode_status = ArtModeStatus.Unavailable
        elif event == "wakeup":
            self._get_artmode_status()
            return
        else:
            # Unknown message
            return

        if self._power_on_requested and artmode_status != ArtModeStatus.Unavailable:
            if artmode_status == ArtModeStatus.On and not self._power_on_artmode:
                self.send_key("KEY_POWER", key_press_delay=0)
            elif artmode_status == ArtModeStatus.Off and self._power_on_artmode:
                self.send_key("KEY_POWER", key_press_delay=0)
            self._power_on_requested = False

        self._artmode_status = artmode_status

    @property
    def is_connected(self):
        return self._is_connected

    @property
    def artmode_status(self):
        return self._artmode_status

    @property
    def installed_app(self):
        return self._installed_app

    @property
    def running_app(self):
        return self._running_app

    def ping_device(self, port=0):
        """Ping TV device to check current status, and return boolean.
            If port is specified, try to open specific port
            for check, otherwise it uses ICMP echo
            If check is True, try to open WS connection
        """
        result = self._ping.ping(port)
        # check ws ping/pong
        call_time = datetime.utcnow()
        if result and self._ws_remote:
            difference = (call_time - self._last_ping).total_seconds()
            result = difference < MAX_WS_PING_INTERVAL

        if not result:
            self.stop_client()
            if self._artmode_status != ArtModeStatus.Unsupported:
                self._artmode_status = ArtModeStatus.Unavailable
        elif self._ws_remote:
            self._check_art_mode()

        if self._power_on_requested:
            difference = (call_time - self._power_on_requested_time).total_seconds()
            if difference > self._power_on_delay:
                self._power_on_requested = False

        return result

    def _check_art_mode(self):
        if self._artmode_status == ArtModeStatus.Unsupported:
            return
        if self._ws_art:
            difference = (datetime.utcnow() - self._last_art_ping).total_seconds()
            if difference >= MAX_WS_PING_INTERVAL:
                self._artmode_status = ArtModeStatus.Unavailable
                self._ws_art.close()
        elif self._ws_remote:
            self.start_client(start_all=True)

    def set_power_on_request(self, set_art_mode=False, power_on_delay=0):
        self._power_on_requested = True
        self._power_on_requested_time = datetime.utcnow()
        self._power_on_artmode = set_art_mode
        self._power_on_delay = max(power_on_delay, 0) or DEFAULT_POWER_ON_DELAY

    def set_power_off_request(self):
        self._power_on_requested = False

    def get_running_app(self, *, force_scan=False):

        if not self._ws_control:
            return

        with self._sync_lock:
            call_time = datetime.utcnow()
            difference = (call_time - self._last_app_scan).total_seconds()
            if (difference < MIN_APP_SCAN_INTERVAL and not force_scan) or difference < 1:
                return
            self._last_app_scan = call_time

        if self._app_list is not None:
            app_to_check = {}
            for app_name, app_id in self._app_list.items():
                app = None
                if self._installed_app:
                    app = self._installed_app.get(app_id)
                else:
                    app_type = self._app_type.get(app_id, 2)
                    if app_type <= 4:
                        app = App(app_id, app_name, app_type)
                if app:
                    app_to_check[app_id] = app
        else:
            app_to_check = self._installed_app

        for app in app_to_check.values():
            self._get_app_status(app.app_id, app.app_type)

    def start_client(self, *, start_all=False):
        """Start all thread that connect to the TV websocket"""

        if self._client_remote is None or not self._client_remote.is_alive():
            self._client_remote = Thread(target=self._client_remote_thread)
            self._client_remote.name = "SamsungRemote"
            self._client_remote.setDaemon(True)
            self._client_remote.start()

            return

        if start_all:
            if self._client_control is None or not self._client_control.is_alive():
                self._client_control = Thread(target=self._client_control_thread)
                self._client_control.name = "SamsungControl"
                self._client_control.setDaemon(True)
                self._client_control.start()

            if self._client_art_supported > 0 and \
               (self._client_art is None or not self._client_art.is_alive()):

                if self._client_art_supported > 1:
                    self._client_art_supported = 0
                self._client_art = Thread(target=self._client_art_thread)
                self._client_art.name = "SamsungArt"
                self._client_art.setDaemon(True)
                self._client_art.start()

    def stop_client(self):
        if self._ws_remote:
            self._ws_remote.close()

    def open(self):
        if self.connection is not None:
            return self.connection

        is_ssl = self._is_ssl_connection()
        url = self._format_websocket_url(
            _WS_ENDPOINT_REMOTE_CONTROL,
            is_ssl=is_ssl
        )
        sslopt = {"cert_reqs": ssl.CERT_NONE} if is_ssl else {}

        _LOGGING.debug("WS url %s", url)
        connection = websocket.create_connection(url, self.timeout, sslopt=sslopt)
        completed = False
        response = ""

        for iteration in range(3):
            response = self._process_api_response(connection.recv())
            _LOGGING.debug(response)
            event = response.get("event", "-")
            if event != "ms.channel.connect":
                break
            conn_data = response.get("data")
            if self._check_conn_id(conn_data):
                completed = True
                token = conn_data.get("token")
                if token:
                    self._set_token(token)
                break

        if not completed:
            self.close()
            raise ConnectionFailure(response)

        self.connection = connection
        return connection

    def close(self):
        if self.connection:
            self.connection.close()
            _LOGGING.debug("Connection closed.")
        self.connection = None

    def send_key(self, key, key_press_delay=None, cmd="Click"):
        _LOGGING.debug("Sending key %s", key)
        return self._ws_send(
            {
                "method": "ms.remote.control",
                "params": {
                    "Cmd": cmd,
                    "DataOfCmd": key,
                    "Option": "false",
                    "TypeOfRemote": "SendRemoteKey",
                },
            },
            key_press_delay,
        )

    def hold_key(self, key, seconds):
        if self.send_key(key, key_press_delay=0, cmd="Press"):
            time.sleep(seconds)
            return self.send_key(key, key_press_delay=0, cmd="Release")
        return False

    def send_text(self, text, send_delay=None):
        if not text:
            return False

        base64_text = self._serialize_string(text)
        if self._ws_send(
            {
                "method": "ms.remote.control",
                "params": {
                    "Cmd": f"{base64_text}",
                    "DataOfCmd": "base64",
                    "TypeOfRemote": "SendInputString",
                },
            },
            key_press_delay=send_delay,
        ):
            self._ws_send(
                {
                    "method": "ms.remote.control",
                    "params": {
                        "TypeOfRemote": "SendInputEnd",
                    },
                },
                key_press_delay=0,
            )
            return True

        return False

    def move_cursor(self, x, y, duration=0):
        self._ws_send(
            {
                "method": "ms.remote.control",
                "params": {
                    "Cmd": "Move",
                    "Position": {"x": x, "y": y, "Time": str(duration)},
                    "TypeOfRemote": "ProcessMouseDevice",
                },
            },
            key_press_delay=0,
        )

    def run_app(self, app_id, action_type="", meta_tag="", *, use_remote=False):

        if not action_type:
            app = self._installed_app.get(app_id)
            if app:
                app_type = app.app_type
            else:
                app_type = self._app_type.get(app_id, 2)
            action_type = TYPE_DEEP_LINK if app_type == 2 else TYPE_NATIVE_LAUNCH
        elif action_type != TYPE_NATIVE_LAUNCH:
            action_type = TYPE_DEEP_LINK

        _LOGGING.debug(
            "Sending run app app_id: %s app_type: %s meta_tag: %s",
            app_id,
            action_type,
            meta_tag,
        )

        if self._ws_control and action_type == TYPE_DEEP_LINK and not use_remote:
            return self._ws_send(
                {
                    "id": app_id,
                    "method": "ms.application.start",
                    "params": {"id": app_id},
                },
                key_press_delay=0,
                use_control=True,
                ws_socket=self._ws_control,
            )

        return self._ws_send(
            {
                "method": "ms.channel.emit",
                "params": {
                    "event": "ed.apps.launch",
                    "to": "host",
                    "data": {
                        # action_type: NATIVE_LAUNCH / DEEP_LINK
                        # app_type == 2 ? 'DEEP_LINK' : 'NATIVE_LAUNCH',
                        "action_type": action_type,
                        "appId": app_id,
                        "metaTag": meta_tag,
                    },
                },
            },
            key_press_delay=0,
        )

    def open_browser(self, url):
        _LOGGING.debug("Opening url in browser %s", url)
        return self.run_app("org.tizen.browser", TYPE_NATIVE_LAUNCH, url)

    def rest_device_info(self):
        _LOGGING.debug("Get device info via rest api")
        response = self._rest_request("")
        return self._process_api_response(response.text, raise_error=False)

    def rest_app_status(self, app_id):
        _LOGGING.debug("Get app %s status via rest api", app_id)
        response = self._rest_request("applications/" + app_id)
        return self._process_api_response(response.text, raise_error=False)

    def rest_app_run(self, app_id):
        _LOGGING.debug("Run app %s via rest api", app_id)
        response = self._rest_request("applications/" + app_id, "POST")
        return self._process_api_response(response.text, raise_error=False)

    def rest_app_close(self, app_id):
        _LOGGING.debug("Close app %s via rest api", app_id)
        response = self._rest_request("applications/" + app_id, "DELETE")
        return self._process_api_response(response.text, raise_error=False)

    def rest_app_install(self, app_id):
        _LOGGING.debug("Install app %s via rest api", app_id)
        response = self._rest_request("applications/" + app_id, "PUT")
        return self._process_api_response(response.text, raise_error=False)

    def shortcuts(self):
        return shortcuts.SamsungTVShortcuts(self)
