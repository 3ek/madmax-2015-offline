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
"""Feed-related Hydra handlers."""

from urllib.parse import unquote

from ..codec import HydraReader, HydraType
from .channels import feed_items_for_channel

_READER = HydraReader()


def _parse_feed_body(body: bytes) -> tuple[str | None, list[str]]:
    """Parse feed request body."""
    if not body:
        return None, []

    pos = 0
    channel: str | None = None
    requested_fields: list[str] = []

    while pos < len(body):
        token_type, value, next_pos = _READER.read_python(body, pos)
        if next_pos <= pos:
            break
        pos = next_pos

        if token_type == HydraType.UTF8 and isinstance(value, str):
            if channel is None:
                channel = value
            else:
                requested_fields.append(value)
        elif token_type == HydraType.ARRAY and isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    requested_fields.append(item)

    return channel, requested_fields


def handle_feed_get_items(body: bytes, source_path: str = "") -> bytes:
    channel = None
    requested_fields: list[str] = []

    if body:
        channel, requested_fields = _parse_feed_body(body)
    elif "/feed/get_items_by_channel/" in source_path:
        tail = source_path.split("/feed/get_items_by_channel/", 1)[1]
        channel = unquote(tail.split("/", 1)[0])

    requested_field = requested_fields[0] if len(requested_fields) == 1 else (requested_fields or None)
    _, response = feed_items_for_channel(str(channel or ""), requested_field=requested_field)
    return response


__all__ = ["handle_feed_get_items"]
