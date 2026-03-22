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
"""HTTPS passthrough implementation for selected upstream domains."""

import http.client
import ssl

from config import PASSTHROUGH_DOMAINS, domain_matches
from lib.helpers import parse_http_headers

from .request_log import log_passthrough_exchange, log_passthrough_summary

_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def is_passthrough_host(host: str) -> bool:
    server_name, _ = split_host_port(host)
    return domain_matches(server_name, PASSTHROUGH_DOMAINS)


def handle_passthrough_request(
    host: str,
    method: str,
    path: str,
    headers_raw: str,
    body: bytes,
) -> tuple[int, str, list[tuple[str, str]], bytes]:
    upstream_host, upstream_port = split_host_port(host)
    forwarded_headers = _build_forward_headers(host, headers_raw)
    context = ssl.create_default_context()
    conn = http.client.HTTPSConnection(
        upstream_host,
        port=upstream_port,
        timeout=20,
        context=context,
    )
    try:
        conn.request(method, path, body=body or None, headers=dict(forwarded_headers))
        response = conn.getresponse()
        response_body = response.read()
        response_headers = _build_response_headers(response.getheaders(), len(response_body))
        log_passthrough_summary(method, host, path, len(body), response.status)
        log_passthrough_exchange(
            method,
            host,
            path,
            headers_raw,
            forwarded_headers,
            body,
            response.status,
            response.reason,
            response_headers,
            response_body,
        )
        return response.status, response.reason, response_headers, response_body
    except Exception as exc:
        error_body = f"Passthrough upstream error for {host}: {exc}\n".encode("utf-8", errors="replace")
        error_headers = [
            ("Content-Type", "text/plain; charset=utf-8"),
            ("Content-Length", str(len(error_body))),
            ("Connection", "close"),
        ]
        log_passthrough_summary(method, host, path, len(body), 502)
        log_passthrough_exchange(
            method,
            host,
            path,
            headers_raw,
            forwarded_headers,
            body,
            502,
            "Bad Gateway",
            error_headers,
            error_body,
        )
        return 502, "Bad Gateway", error_headers, error_body
    finally:
        conn.close()


def split_host_port(host: str) -> tuple[str, int]:
    host = host.strip().lower()
    if not host:
        return "", 443
    if host.startswith("[") and "]" in host:
        end = host.index("]")
        server_name = host[1:end]
        port_part = host[end + 1:]
        if port_part.startswith(":") and port_part[1:].isdigit():
            return server_name, int(port_part[1:])
        return server_name, 443
    if ":" in host:
        server_name, maybe_port = host.rsplit(":", 1)
        if maybe_port.isdigit():
            return server_name, int(maybe_port)
    return host, 443


def _build_forward_headers(host: str, headers_raw: str) -> list[tuple[str, str]]:
    headers = []
    for name, value in parse_http_headers(headers_raw):
        lowered = name.lower()
        if lowered in _HOP_BY_HOP_HEADERS or lowered == "content-length":
            continue
        if lowered == "host":
            continue
        headers.append((name, value))
    headers.append(("Host", host))
    headers.append(("Connection", "close"))
    return headers


def _build_response_headers(headers: list[tuple[str, str]], body_length: int) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    for name, value in headers:
        lowered = name.lower()
        if lowered in _HOP_BY_HOP_HEADERS or lowered == "content-length":
            continue
        output.append((name, value))
    output.append(("Content-Length", str(body_length)))
    output.append(("Connection", "close"))
    return output
