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
"""Hydra codec package."""

from .decode import HydraReader, parse_wrapped_body
from .encode import HydraWriter, wrap_hex_body, wrap_value
from .types import HydraType
from .values import (
    HydraArray,
    HydraBinary,
    HydraBitStruct,
    HydraBool,
    HydraDateTime,
    HydraFloat64,
    HydraHashMap,
    HydraInt32,
    HydraInt64,
    HydraNone,
    HydraStruct,
    HydraUInt64,
    HydraUnsignedByte,
    HydraUtf8,
    HydraValue,
)

__all__ = [
    "HydraType",
    "HydraValue",
    "HydraNone",
    "HydraInt32",
    "HydraBinary",
    "HydraBool",
    "HydraUnsignedByte",
    "HydraFloat64",
    "HydraDateTime",
    "HydraArray",
    "HydraStruct",
    "HydraInt64",
    "HydraBitStruct",
    "HydraHashMap",
    "HydraUInt64",
    "HydraUtf8",
    "HydraWriter",
    "HydraReader",
    "wrap_value",
    "wrap_hex_body",
    "parse_wrapped_body",
]
