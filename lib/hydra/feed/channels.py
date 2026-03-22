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
"""Feed payload builders modeled after My Steelport FeedModule."""

from ..codec import HydraWriter
from .legal import handle_legal_channel
from .payloads import handle_feed_channel

_WRITER = HydraWriter()


def feed_items_for_channel(
    channel: str,
    requested_field: str | list[str] | None = None,
) -> tuple[str, bytes]:
    channel = str(channel or "")
    legal = handle_legal_channel(channel)
    if legal is not None:
        return "legal", legal
    feed = handle_feed_channel(channel, requested_field)
    if feed is not None:
        return feed
    return "empty", _WRITER.write([])
