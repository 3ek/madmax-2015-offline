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
"""Hydra wire decoding helpers."""

from __future__ import annotations

import datetime as _dt
import struct
from typing import Any

from . import values
from .types import HydraType


def parse_wrapped_body(body: bytes) -> tuple[int, bytes] | None:
    if len(body) < 5:
        return None
    prefix_byte = body[0]
    inner_len = struct.unpack(">I", body[1:5])[0]
    try:
        inner = bytes.fromhex(body[5:5 + inner_len].decode("ascii"))
    except Exception:
        return None
    return prefix_byte, inner


def _read_length_prefixed_bytes(data: bytes, pos: int) -> tuple[bytes, int]:
    size = struct.unpack_from(">I", data, pos)[0]
    pos += 4
    value = data[pos:pos + size]
    pos += size
    return value, pos


class HydraReader:
    def read(self, data: bytes, pos: int = 0) -> tuple[values.HydraValue, int]:
        token_type = data[pos]
        pos += 1

        if token_type == HydraType.UTF8:
            raw, pos = _read_length_prefixed_bytes(data, pos)
            return values.HydraUtf8(raw.decode("utf-8", errors="replace")), pos
        if token_type == HydraType.INT32:
            value = struct.unpack_from(">i", data, pos)[0]
            pos += 4
            return values.HydraInt32(value), pos
        if token_type == HydraType.BINARY:
            value, pos = _read_length_prefixed_bytes(data, pos)
            return values.HydraBinary(value), pos
        if token_type == HydraType.BOOL:
            value = data[pos] != 0
            pos += 1
            return values.HydraBool(value), pos
        if token_type == HydraType.UNSIGNED_BYTE:
            value = data[pos]
            pos += 1
            return values.HydraUnsignedByte(value), pos
        if token_type == HydraType.FLOAT64:
            value = struct.unpack_from(">d", data, pos)[0]
            pos += 8
            return values.HydraFloat64(value), pos
        if token_type == HydraType.DATETIME:
            timestamp = struct.unpack_from(">I", data, pos)[0]
            pos += 4
            return values.HydraDateTime(_dt.datetime.fromtimestamp(timestamp, tz=_dt.timezone.utc)), pos
        if token_type == HydraType.ARRAY:
            count = struct.unpack_from(">I", data, pos)[0]
            pos += 4
            items = []
            for _ in range(count):
                item, pos = self.read(data, pos)
                items.append(item)
            return values.HydraArray(items), pos
        if token_type == HydraType.STRUCT:
            return self._read_mapping(data, pos, values.HydraStruct)
        if token_type == HydraType.INT64:
            value = struct.unpack_from(">q", data, pos)[0]
            pos += 8
            return values.HydraInt64(value), pos
        if token_type == HydraType.BITSTRUCT:
            value, pos = _read_length_prefixed_bytes(data, pos)
            return values.HydraBitStruct(value), pos
        if token_type == HydraType.HASHMAP:
            return self._read_mapping(data, pos, values.HydraHashMap)
        if token_type == HydraType.UINT64:
            value = struct.unpack_from(">Q", data, pos)[0]
            pos += 8
            return values.HydraUInt64(value), pos
        if token_type == HydraType.NONE:
            return values.HydraNone(), pos
        raise ValueError(f"Unsupported Hydra token type: 0x{token_type:02x}")

    def _read_mapping(
        self,
        data: bytes,
        pos: int,
        mapping_cls: type[values.HydraStruct] | type[values.HydraHashMap],
    ) -> tuple[values.HydraStruct | values.HydraHashMap, int]:
        count = struct.unpack_from(">I", data, pos)[0]
        pos += 4
        value: dict[str, Any] = {}
        for _ in range(count):
            key, pos = self.read(data, pos)
            if not isinstance(key, values.HydraUtf8):
                raise ValueError(f"Hydra hash key is not Utf8String: 0x{int(key.hydra_type):02x}")
            item, pos = self.read(data, pos)
            value[str(key)] = item
        return mapping_cls(value), pos

    def read_python_token(self, data: bytes, pos: int) -> tuple[int, Any, int]:
        token, pos = self.read(data, pos)
        return int(token.hydra_type), token.to_python(), pos

    def read_python(self, data: bytes, pos: int = 0) -> tuple[int, Any, int]:
        return self.read_python_token(data, pos)

__all__ = [
    "HydraReader",
    "parse_wrapped_body",
]
