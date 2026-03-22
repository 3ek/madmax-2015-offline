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
"""Logging helpers for HTTPS passthrough traffic."""

import datetime as dt
from pathlib import Path

from lib import config_runtime

LOG_DIR = Path(__file__).resolve().parents[2] / "hydra_logs"
SESSION_TS = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
LOG_FILE = LOG_DIR / f"passthrough_{SESSION_TS}.log"
SUMMARY_FILE = LOG_DIR / f"passthrough_all_{SESSION_TS}.log"


def xxd(data: bytes, width: int = 16) -> str:
    lines = []
    for offset in range(0, len(data), width):
        chunk = data[offset:offset + width]
        hex_part = " ".join(f"{byte:02x}" for byte in chunk)
        ascii_part = "".join(chr(byte) if 32 <= byte < 127 else "." for byte in chunk)
        lines.append(f"  {offset:08x}  {hex_part:<{width * 3}}  |{ascii_part}|")
    return "\n".join(lines)


def _headers_text(headers: list[tuple[str, str]]) -> str:
    if not headers:
        return "  (empty)"
    return "\n".join(f"{name}: {value}" for name, value in headers)


def _body_text(body: bytes) -> str:
    if not body:
        return "  (empty)"
    return body.decode("utf-8", errors="replace")


def log_passthrough_summary(method: str, host: str, path: str, body_size: int, status_code: int) -> None:
    if not config_runtime.DEBUG:
        return
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = dt.datetime.now().isoformat(timespec="milliseconds")
    with open(SUMMARY_FILE, "a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} {method} https://{host}{path} ({body_size}b) -> {status_code}\n")


def log_passthrough_exchange(
    method: str,
    host: str,
    path: str,
    client_headers_raw: str,
    forwarded_headers: list[tuple[str, str]],
    request_body: bytes,
    status_code: int,
    reason: str,
    response_headers: list[tuple[str, str]],
    response_body: bytes,
) -> None:
    if not config_runtime.DEBUG:
        return
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = dt.datetime.now().isoformat(timespec="milliseconds")
    lines = [
        "=" * 72,
        f"  {timestamp}  {method} https://{host}{path}  body={len(request_body)}b",
        "=" * 72,
        "-- Client headers --",
        client_headers_raw.strip(),
        "",
        "-- Forwarded headers --",
        _headers_text(forwarded_headers),
        "",
        "-- Request body --",
        xxd(request_body) if request_body else "  (empty)",
        "",
        "-- Request text --",
        _body_text(request_body),
        "",
        "-- Request hex --",
        f"  {request_body.hex()}",
        "",
        "-- Response status --",
        f"  {status_code} {reason}",
        "",
        "-- Response headers --",
        _headers_text(response_headers),
        "",
        "-- Response body --",
        xxd(response_body) if response_body else "  (empty)",
        "",
        "-- Response text --",
        _body_text(response_body),
        "",
        "-- Response hex --",
        f"  {response_body.hex()}",
        "",
    ]
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
