# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025  madmax-2015-offline contributors
#
# This file is part of madmax-2015-offline.
#
# madmax-2015-offline is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# madmax-2015-offline is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""HTTPS server entry point for Hydra and Turbine traffic."""

import socket
import ssl
import threading
import traceback

from config import HTTPS_PORT
from lib.helpers import read_http_request, send_http_response, send_http_response_raw
from lib.hydra_api import handle_hydra_request
from lib.passthrough import handle_passthrough_request, is_passthrough_host
from lib.turbine import handle_turbine_request, is_turbine_host, log_all_request

_REASONS = {
    200: "OK",
    201: "Created",
    204: "No Content",
    502: "Bad Gateway",
    404: "Not Found",
    409: "Conflict",
}


def handle_connection(conn: socket.socket, addr, ctx: ssl.SSLContext) -> None:
    try:
        tls = ctx.wrap_socket(conn, server_side=True)
        print(f"[TLS]  Connected {addr}")
        headers_raw, body = read_http_request(tls)
        if not headers_raw:
            print(f"[TLS]  No data received from {addr}")
            return
        method, path = _parse_request_line(headers_raw)
        print(f"[TLS]  {method} {path}  ({len(body)}b body)")
        log_all_request(method, path, len(body))
        host = _extract_host(headers_raw)
        if is_passthrough_host(host):
            status_code, reason, response_headers, response_body = handle_passthrough_request(
                host,
                method,
                path,
                headers_raw,
                body,
            )
            send_http_response_raw(tls, status_code, reason, response_headers, response_body)
        elif is_turbine_host(host):
            status_code, response_body, response_type = handle_turbine_request(method, path, headers_raw, body)
            reason = _REASONS.get(status_code, "OK")
            send_http_response(tls, f"{status_code} {reason}", response_type, response_body)
        else:
            status_code, response_body = handle_hydra_request(path, headers_raw, body)
            response_type = "application/x-hydra-binary"
            reason = _REASONS.get(status_code, "OK")
            send_http_response(tls, f"{status_code} {reason}", response_type, response_body)
    except ssl.SSLError as exc:
        print(f"[TLS]  SSL error {addr}: {exc}")
    except Exception as exc:
        print(f"[TLS]  Error {addr}: {exc}")
        traceback.print_exc()
    finally:
        try:
            conn.close()
        except Exception:
            pass


def https_server_loop(ctx: ssl.SSLContext) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", HTTPS_PORT))
    sock.listen(10)
    print(f"[HTTPS] Listening on TCP 0.0.0.0:{HTTPS_PORT}")
    while True:
        try:
            conn, addr = sock.accept()
            thread = threading.Thread(
                target=handle_connection,
                args=(conn, addr, ctx),
                daemon=True,
            )
            thread.start()
        except Exception as exc:
            print(f"[HTTPS] Accept error: {exc}")


def _parse_request_line(headers_raw: str) -> tuple[str, str]:
    first_line = headers_raw.split("\r\n", 1)[0]
    parts = first_line.split(" ")
    method = parts[0] if len(parts) > 0 else ""
    path = parts[1] if len(parts) > 1 else "/"
    return method, path


def _extract_host(headers_raw: str) -> str:
    for line in headers_raw.split("\r\n"):
        if line.lower().startswith("host:"):
            return line.split(":", 1)[1].strip().lower()
    return ""
