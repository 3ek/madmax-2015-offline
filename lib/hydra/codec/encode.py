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
"""Hydra wire encoding helpers."""

from __future__ import annotations

import datetime as _dt
import struct

from . import values

_MISSING = object()
wrap_value = values.wrap_value


class HydraWriter:
    def __init__(self, value: object = _MISSING):
        self._value = value

    def coerce(self, value: object = _MISSING) -> values.HydraValue:
        if value is _MISSING:
            if self._value is _MISSING:
                raise ValueError("HydraWriter has no value to encode")
            value = self._value
        return values.wrap_value(value)

    def to_value(self, value: object = _MISSING) -> values.HydraValue:
        return self.coerce(value)

    def write(self, value: object = _MISSING) -> bytes:
        return bytes(self.coerce(value))

    def encode(self, value: object = _MISSING) -> bytes:
        return self.write(value)

    def __bytes__(self) -> bytes:
        return self.write()

    def __call__(self, value: object = _MISSING) -> bytes:
        return self.write(value)


def wrap_hex_body(prefix_byte: int, body: bytes) -> bytes:
    hex_body = body.hex().upper().encode("ascii")
    return bytes([prefix_byte]) + struct.pack(">I", len(hex_body)) + hex_body


__all__ = [
    "HydraWriter",
    "wrap_value",
    "wrap_hex_body",
]
