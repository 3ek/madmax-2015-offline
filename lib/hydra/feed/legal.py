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
"""Legal feed payload builders for TOS_PL and PP_PL channels.

Confirmed behaviour: returning an empty ARRAY causes the game to treat
TOS/PP as already accepted and proceed normally.
"""

from ..codec import HydraWriter

_WRITER = HydraWriter()


def handle_legal_channel(channel: str) -> bytes | None:
    channel = str(channel or "").upper()
    if channel.startswith("TOS") or channel.startswith("PP"):
        print(f"[FEED] {channel} -> empty array (TOS/PP accepted)")
        return _WRITER.write([])
    return None
