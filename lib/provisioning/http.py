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
"""HTTP response helpers for the provisioning server."""


def send_response(
    conn,
    status: str,
    body: bytes | str,
    *,
    content_type: str,
    content_disposition: str | None = None,
) -> None:
    if isinstance(body, str):
        body = body.encode("utf-8")
    headers = [
        f"HTTP/1.1 {status}",
        f"Content-Type: {content_type}",
    ]
    if content_disposition:
        headers.append(f"Content-Disposition: {content_disposition}")
    headers.extend([
        f"Content-Length: {len(body)}",
        "Connection: close",
        "",
        "",
    ])
    conn.sendall("\r\n".join(headers).encode("utf-8") + body)
