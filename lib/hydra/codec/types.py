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
"""Shared Hydra token identifiers."""

from __future__ import annotations

from enum import IntEnum


class HydraType(IntEnum):
    NONE = 0x01
    INT32 = 0x02
    BINARY = 0x03
    BOOL = 0x04
    UNSIGNED_BYTE = 0x05
    FLOAT64 = 0x06
    DATETIME = 0x07
    ARRAY = 0x08
    STRUCT = 0x09
    INT64 = 0x0A
    BITSTRUCT = 0x0B
    HASHMAP = 0x0C
    UINT64 = 0x0D
    UTF8 = 0x0E

__all__ = [
    "HydraType",
]
