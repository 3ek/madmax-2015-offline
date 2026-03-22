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
"""
Shared helper utilities used across multiple modules.
"""

import subprocess


def run_cmd(cmd: str, **kwargs) -> str:
    """Run a shell command, raise RuntimeError on failure, return stdout."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{result.stderr}")
    return result.stdout.strip()


def build_http_response_headers(status: str, content_type: str, body_length: int) -> str:
    return (
        f"HTTP/1.1 {status}\r\n"
        f"Accept: {content_type}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Accept-Language: pl,en-US;q=0.9,en;q=0.8\r\n"
        f"X-Hydra-Error-Code: 200\r\n"
        f"X-Hydra-Processing-Time: 123\r\n"
        f"Content-Length: {body_length}\r\n"
        f"Connection: Keep-Alive\r\n"
        f"\r\n"
    )


def send_http_response(sock, status: str, content_type: str, body: bytes | str) -> None:
    """Send a bare HTTP/1.1 response over *sock* (plain or TLS socket)."""
    if isinstance(body, str):
        body = body.encode("utf-8")
    response = build_http_response_headers(status, content_type, len(body)).encode() + body
    sock.sendall(response)


def send_http_response_raw(
    sock,
    status_code: int,
    reason: str,
    headers: list[tuple[str, str]],
    body: bytes | str,
) -> None:
    """Send a raw HTTP/1.1 response using the provided status line and headers."""
    if isinstance(body, str):
        body = body.encode("utf-8")
    status_line = f"HTTP/1.1 {status_code} {reason}\r\n"
    header_lines = "".join(f"{name}: {value}\r\n" for name, value in headers)
    sock.sendall(status_line.encode("ascii") + header_lines.encode("utf-8") + b"\r\n" + body)


def read_http_request(sock) -> tuple[str, bytes]:
    """
    Read a complete HTTP request (headers + body) from *sock*.
    Returns (headers_raw, body_bytes).
    """
    data = b""
    sock.settimeout(5.0)
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"\r\n\r\n" in data:
                header_end = data.index(b"\r\n\r\n") + 4
                headers_raw = data[:header_end].decode("utf-8", errors="replace")
                cl = 0
                for line in headers_raw.split("\r\n"):
                    if line.lower().startswith("content-length:"):
                        cl = int(line.split(":", 1)[1].strip())
                body = data[header_end:]
                while len(body) < cl:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    body += chunk
                return headers_raw, body
    except TimeoutError:
        pass
    return data.decode("utf-8", errors="replace"), b""


def parse_http_headers(headers_raw: str) -> list[tuple[str, str]]:
    """Parse HTTP headers from a raw request/response block, excluding the start line."""
    headers: list[tuple[str, str]] = []
    for line in headers_raw.split("\r\n")[1:]:
        if not line:
            break
        if ":" not in line:
            continue
        name, value = line.split(":", 1)
        headers.append((name.strip(), value.strip()))
    return headers
