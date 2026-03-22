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
"""Small request logging helpers used by the HTTPS/Turbine path."""

import datetime as dt
from pathlib import Path

from lib import config_runtime

SESSION_START = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / f"turbine_{SESSION_START}.log"


def xxd(data: bytes, width: int = 16) -> str:
    lines = []
    for offset in range(0, len(data), width):
        chunk = data[offset:offset + width]
        hex_part = " ".join(f"{byte:02x}" for byte in chunk)
        ascii_part = "".join(chr(byte) if 32 <= byte < 127 else "." for byte in chunk)
        lines.append(f"  {offset:08x}  {hex_part:<{width * 3}}  |{ascii_part}|")
    return "\n".join(lines)


def log_all_request(method: str, path: str, body_size: int) -> None:
    if not config_runtime.DEBUG:
        return
    LOG_DIR.mkdir(exist_ok=True)
    log_path = LOG_DIR / f"all_requests_{SESSION_START}.log"
    with open(log_path, "a", encoding="utf-8") as handle:
        timestamp = dt.datetime.now().isoformat()
        handle.write(f"{timestamp} {method} {path} ({body_size}b)\n")


def log_turbine_request(path: str, headers_raw: str, body: bytes, response: bytes | str | None) -> None:
    if not config_runtime.DEBUG:
        return
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = dt.datetime.now().isoformat(timespec="milliseconds")
    body_text = body.decode("utf-8", errors="replace") if body else "(empty)"
    if isinstance(response, (bytes, bytearray)):
        response_bytes = bytes(response)
        response_text = response_bytes.decode("utf-8", errors="replace") if response_bytes else "(empty)"
        response_hex = response_bytes.hex()
    elif isinstance(response, str):
        response_text = response or "(empty)"
        response_hex = response.encode("utf-8").hex()
    elif response is None:
        response_text = "(empty)"
        response_hex = ""
    else:
        response_text = repr(response)
        response_hex = ""
    lines = [
        "=" * 72,
        f"  {timestamp}  {path}  body={len(body)}b",
        "=" * 72,
        "-- Headers --",
        headers_raw.strip(),
        "",
        "-- Body -----",
        xxd(body) if body else "  (empty)",
        "",
        "-- Body text",
        f"  {body_text}" if body else "  (empty)",
        "",
        "-- Body hex -",
        f"  {body.hex()}",
        "",
        "-- Response -",
        f"  {response_text}",
        "",
        "-- Response hex -",
        f"  {response_hex}" if response_hex else "  (empty)",
        "",
    ]
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def log_turbine_xml(body: bytes) -> None:
    if not config_runtime.DEBUG:
        return
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = dt.datetime.now().strftime("%H%M%S_%f")
    (LOG_DIR / f"turbine_{timestamp}.xml").write_bytes(body)
