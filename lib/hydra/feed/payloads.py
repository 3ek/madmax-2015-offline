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
"""Feed payload builder backed by data/feeds/<CHANNEL>.json."""

from ..codec import HydraWriter
from .store import load_feed

_WRITER = HydraWriter()


def _encode_value(value):
    """Convert a JSON value to a typed Hydra value."""
    return _WRITER.coerce(value)


def handle_feed_channel(
    channel: str,
    requested_field: str | list[str] | None = None,
) -> tuple[str, bytes] | None:
    """
    Build feed response based on data/feeds/<channel>.json.
    Only encodes fields that the game requested.
    Auto-creates/updates the JSON file for unknown fields.
    """
    if isinstance(requested_field, list):
        requested_fields: list[str] = requested_field
    elif requested_field:
        requested_fields = [requested_field]
    else:
        requested_fields = []

    data = load_feed(channel, requested_fields)

    pairs: dict[str, object] = {}
    if requested_fields:
        for field in requested_fields:
            val = data.get(field, "")
            pairs[field] = _encode_value(val)
    else:
        for field, val in data.items():
            pairs[field] = _encode_value(val)

    if not pairs:
        return None

    payload = _WRITER.write(pairs)
    print(f"[FEED] {channel}  fields={requested_fields}  {len(payload)}b")
    return f"{channel.lower()}_datastore", payload
