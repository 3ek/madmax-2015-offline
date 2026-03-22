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
"""Hydra request logging helpers."""

import datetime
from pathlib import Path

from lib import config_runtime
from lib.helpers import build_http_response_headers

LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
SESSION_TS = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
LOG_FILE = LOG_DIR / f"{SESSION_TS}.log"
REASONS = {
    200: "OK",
    201: "Created",
    204: "No Content",
    404: "Not Found",
    409: "Conflict",
}


def xxd(data: bytes, width: int = 16) -> str:
    lines = []
    for offset in range(0, len(data), width):
        chunk = data[offset:offset + width]
        hex_part = " ".join(f"{byte:02x}" for byte in chunk)
        ascii_part = "".join(chr(byte) if 32 <= byte < 127 else "." for byte in chunk)
        lines.append(f"  {offset:08x}  {hex_part:<{width * 3}}  |{ascii_part}|")
    return "\n".join(lines)


def _response_bytes(response: bytes | str | None) -> bytes:
    if response is None:
        return b""
    if isinstance(response, str):
        return response.encode("utf-8")
    return bytes(response)


def log_request(
    path: str,
    headers_raw: str,
    body: bytes,
    response: bytes | str | None,
    *,
    status_code: int = 200,
    response_type: str = "application/x-hydra-binary",
) -> None:
    if not config_runtime.DEBUG:
        return
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().isoformat(timespec="milliseconds")
    response_bytes = _response_bytes(response)
    response_status = f"{status_code} {REASONS.get(status_code, 'OK')}"
    response_headers = build_http_response_headers(response_status, response_type, len(response_bytes)).strip()
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
        "-- Body hex -",
        f"  {body.hex()}",
        "",
        "-- Response headers --",
        response_headers,
        "",
        "-- Response body ---",
        xxd(response_bytes) if response_bytes else "  (empty)",
        "",
        "-- Response hex ----",
        f"  {response_bytes.hex()}",
        "",
    ]
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
