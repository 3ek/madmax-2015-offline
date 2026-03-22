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
"""Profile time conversion helpers.

The game uses YYYYMMDDHHmmss (UTC) as an integer for timestamp fields.
Example: 2026-03-21 07:41:37 UTC -> 20260321074137
"""

from datetime import datetime, timezone


def game_time_to_datetime(value: int | str) -> datetime:
    text = str(int(value))
    if len(text) != 14:
        raise ValueError(f"Unsupported game time format: {value!r}")
    return datetime.strptime(text, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)


def datetime_to_game_time(value: datetime) -> int:
    dt = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    return int(dt.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S"))


def current_game_time() -> int:
    """Return current UTC time as YYYYMMDDHHmmss integer."""
    return datetime_to_game_time(datetime.now(timezone.utc))
