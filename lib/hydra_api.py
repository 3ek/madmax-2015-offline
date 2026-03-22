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
Hydra SDK request entry point.

This file stays as the public facade used by the rest of the project while
most protocol-specific helpers live in `hydra/`. The split keeps the main
entry point readable and small enough to navigate, but still large enough to
show the actual routing flow in one place.

Wire format summary:
  Wrapped binary body: prefix(1b) | BE-uint32(hex_len) | ASCII-hex-string
  Inner payload: wrapped binary or Hydra key-value tokens depending on endpoint

Main handled routes:
  /auth/pc_steam
  /profile/create
  /profile/get
  /profile/get_by_platform_account_id
  /profile/update
  /feed/get_items_by_channel
  /event_log/create_events
"""

from lib.hydra.codec import HydraInt64, HydraType, HydraWriter, parse_wrapped_body
from lib.hydra.handlers_auth import (
    handle_auth_pc_steam,
    handle_heartbeat,
    handle_spawn_error,
)
from lib.hydra.feed.handlers import handle_feed_get_items
from lib.hydra.profile import store as profile_store
from lib.hydra.profile.handlers import (
    handle_profile_create,
    handle_profile_get,
    handle_profile_get_by_platform,
    handle_profile_update,
)
from lib.hydra.request_log import log_request

_WRITER = HydraWriter()


def handle_hydra_request(path: str, headers_raw: str, body: bytes) -> tuple[int, bytes]:
    if "/profile/" in path:
        return _handle_profile_route(path, headers_raw, body)

    if "/feed/get_items_by_channel" in path:
        return _handle_feed_route(path, headers_raw, body)

    if "/event_log/create_events" in path:
        return _logged(200, path, headers_raw, body, b"\x01")

    return _handle_wrapped_route(path, headers_raw, body)


def _handle_profile_route(path: str, headers_raw: str, body: bytes) -> tuple[int, bytes]:
    if "/profile/create" in path:
        return _handle_profile_create_path(path, headers_raw, body)
    if "/profile/get_by_platform_account_id" in path:  # must be before /profile/get
        return _logged(200, path, headers_raw, body, handle_profile_get_by_platform(body))
    if path.split("?")[0].endswith("/profile/get") or "/profile/get/" in path:
        return _logged(200, path, headers_raw, body, handle_profile_get(body))
    if "/profile/update" in path:
        inner = body  # full body: [UINT64 guid] [STRUCT updates]
        return _logged(200, path, headers_raw, body, handle_profile_update(inner))
    return _logged(200, path, headers_raw, body, b"")


def _handle_feed_route(path: str, headers_raw: str, body: bytes) -> tuple[int, bytes]:
    return _logged(200, path, headers_raw, body, handle_feed_get_items(body, path))


def _handle_wrapped_route(path: str, headers_raw: str, body: bytes) -> tuple[int, bytes]:
    parsed = parse_wrapped_body(body)
    if parsed is None:
        return _logged(200, path, headers_raw, body, b"")
    wrapper_prefix, inner = parsed

    if "/auth/pc_steam" in path:
        response = handle_auth_pc_steam(wrapper_prefix, inner)
    else:
        response = b""
    return _logged(200, path, headers_raw, body, response)


def _handle_profile_create_path(path: str, headers_raw: str, body: bytes) -> tuple[int, bytes]:
    if body and body[0] == HydraType.UTF8:
        platform_id, _, _ = profile_store.parse_profile_get_probe_body(body)
        response = handle_profile_get_by_platform(body) if platform_id else _WRITER.write(HydraInt64(1))
        return _logged(200, path, headers_raw, body, response)
    response = handle_profile_create(body)
    return _logged(200, path, headers_raw, body, response)


def _logged(status: int, path: str, headers_raw: str, body: bytes, response: bytes) -> tuple[int, bytes]:
    log_request(path, headers_raw, body, response)
    return status, response


__all__ = ["handle_hydra_request"]
