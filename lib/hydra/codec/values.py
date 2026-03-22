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
"""Typed Hydra value wrappers."""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Any, ClassVar, Iterator

from .types import HydraType

EPOCH = _dt.datetime(1970, 1, 1, tzinfo=_dt.timezone.utc)


def _coerce_bytes(value: bytes | bytearray | memoryview) -> bytes:
    return bytes(value)


def _encode_u32(value: int) -> bytes:
    return int(value).to_bytes(4, "big", signed=False)


def _encode_token(value: Any) -> bytes:
    wrapped = wrap_value(value)
    return bytes(wrapped)


def _to_python(value: Any) -> Any:
    if isinstance(value, HydraValue):
        return value.to_python()
    if isinstance(value, list):
        return [_to_python(item) for item in value]
    if isinstance(value, tuple):
        return [_to_python(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _to_python(item) for key, item in value.items()}
    return value


@dataclass(slots=True)
class HydraValue:
    """Base class for a typed Hydra token wrapper."""

    value: Any
    hydra_type: ClassVar[HydraType]

    def __bytes__(self) -> bytes:
        return bytes([int(self.hydra_type)]) + self._encode_payload()

    def _encode_payload(self) -> bytes:
        raise NotImplementedError

    def to_python(self) -> Any:
        return _to_python(self.value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value!r})"


@dataclass(slots=True)
class HydraNone(HydraValue):
    hydra_type = HydraType.NONE

    def __init__(self, value: None = None):
        HydraValue.__init__(self, None)

    def _encode_payload(self) -> bytes:
        return b""

    def __bool__(self) -> bool:
        return False


@dataclass(slots=True)
class HydraInt32(HydraValue):
    hydra_type = HydraType.INT32

    def __int__(self) -> int:
        return int(self.value)

    def _encode_payload(self) -> bytes:
        return int(self.value).to_bytes(4, "big", signed=True)


@dataclass(slots=True)
class HydraBinary(HydraValue):
    hydra_type = HydraType.BINARY

    def __bytes__(self) -> bytes:
        return bytes([int(self.hydra_type)]) + self._encode_payload()

    def _encode_payload(self) -> bytes:
        raw = _coerce_bytes(self.value)
        return _encode_u32(len(raw)) + raw

    def __len__(self) -> int:
        return len(_coerce_bytes(self.value))


@dataclass(slots=True)
class HydraBool(HydraValue):
    hydra_type = HydraType.BOOL

    def __bool__(self) -> bool:
        return bool(self.value)

    def _encode_payload(self) -> bytes:
        return b"\x01" if bool(self.value) else b"\x00"


@dataclass(slots=True)
class HydraUnsignedByte(HydraValue):
    hydra_type = HydraType.UNSIGNED_BYTE

    def __int__(self) -> int:
        return int(self.value)

    def _encode_payload(self) -> bytes:
        return bytes([int(self.value) & 0xFF])


@dataclass(slots=True)
class HydraFloat64(HydraValue):
    hydra_type = HydraType.FLOAT64

    def __float__(self) -> float:
        return float(self.value)

    def _encode_payload(self) -> bytes:
        import struct

        return struct.pack(">d", float(self.value))


@dataclass(slots=True)
class HydraDateTime(HydraValue):
    hydra_type = HydraType.DATETIME

    def __int__(self) -> int:
        if isinstance(self.value, _dt.datetime):
            dt = self.value if self.value.tzinfo is not None else self.value.replace(tzinfo=_dt.timezone.utc)
            return int(round((dt.astimezone(_dt.timezone.utc) - EPOCH).total_seconds()))
        return int(self.value)

    def _encode_payload(self) -> bytes:
        return int(self).to_bytes(4, "big", signed=False)


@dataclass(slots=True)
class HydraArray(HydraValue):
    hydra_type = HydraType.ARRAY

    value: list[Any]

    def __iter__(self) -> Iterator[Any]:
        return iter(self.value)

    def __getitem__(self, index: int) -> Any:
        return self.value[index]

    def __len__(self) -> int:
        return len(self.value)

    def _encode_payload(self) -> bytes:
        raw_items = b"".join(_encode_token(item) for item in self.value)
        return _encode_u32(len(self.value)) + raw_items


@dataclass(slots=True)
class HydraStruct(HydraValue):
    hydra_type = HydraType.STRUCT

    value: dict[str, Any]

    def __iter__(self) -> Iterator[str]:
        return iter(self.value)

    def __getitem__(self, key: str) -> Any:
        return self.value[key]

    def __len__(self) -> int:
        return len(self.value)

    def items(self):
        return self.value.items()

    def keys(self):
        return self.value.keys()

    def values(self):
        return self.value.values()

    def get(self, key: str, default: Any = None) -> Any:
        return self.value.get(key, default)

    def _encode_payload(self) -> bytes:
        body = _encode_u32(len(self.value))
        for key, item in self.value.items():
            body += bytes(HydraUtf8(str(key)))
            body += _encode_token(item)
        return body


@dataclass(slots=True)
class HydraInt64(HydraValue):
    hydra_type = HydraType.INT64

    def __int__(self) -> int:
        return int(self.value)

    def _encode_payload(self) -> bytes:
        return int(self.value).to_bytes(8, "big", signed=True)


@dataclass(slots=True)
class HydraBitStruct(HydraValue):
    hydra_type = HydraType.BITSTRUCT

    def _encode_payload(self) -> bytes:
        raw = _coerce_bytes(self.value)
        return _encode_u32(len(raw)) + raw

    def __len__(self) -> int:
        return len(_coerce_bytes(self.value))


@dataclass(slots=True)
class HydraHashMap(HydraValue):
    hydra_type = HydraType.HASHMAP

    value: dict[str, Any]

    def __iter__(self) -> Iterator[str]:
        return iter(self.value)

    def __getitem__(self, key: str) -> Any:
        return self.value[key]

    def __len__(self) -> int:
        return len(self.value)

    def items(self):
        return self.value.items()

    def keys(self):
        return self.value.keys()

    def values(self):
        return self.value.values()

    def get(self, key: str, default: Any = None) -> Any:
        return self.value.get(key, default)

    def _encode_payload(self) -> bytes:
        body = _encode_u32(len(self.value))
        for key, item in self.value.items():
            body += bytes(HydraUtf8(str(key)))
            body += _encode_token(item)
        return body


@dataclass(slots=True)
class HydraUInt64(HydraValue):
    hydra_type = HydraType.UINT64

    def __int__(self) -> int:
        return int(self.value)

    def _encode_payload(self) -> bytes:
        return int(self.value).to_bytes(8, "big", signed=False)


@dataclass(slots=True)
class HydraUtf8(HydraValue):
    hydra_type = HydraType.UTF8

    def __str__(self) -> str:
        return str(self.value)

    def _encode_payload(self) -> bytes:
        raw = str(self.value).encode("utf-8")
        return _encode_u32(len(raw)) + raw


HYDRA_TYPE_TO_VALUE_CLASS: dict[HydraType, type[HydraValue]] = {
    HydraType.NONE: HydraNone,
    HydraType.INT32: HydraInt32,
    HydraType.BINARY: HydraBinary,
    HydraType.BOOL: HydraBool,
    HydraType.UNSIGNED_BYTE: HydraUnsignedByte,
    HydraType.FLOAT64: HydraFloat64,
    HydraType.DATETIME: HydraDateTime,
    HydraType.ARRAY: HydraArray,
    HydraType.STRUCT: HydraStruct,
    HydraType.INT64: HydraInt64,
    HydraType.BITSTRUCT: HydraBitStruct,
    HydraType.HASHMAP: HydraHashMap,
    HydraType.UINT64: HydraUInt64,
    HydraType.UTF8: HydraUtf8,
}

HYDRA_VALUE_CLASS_TO_TYPE: dict[type[HydraValue], HydraType] = {
    cls: hydra_type for hydra_type, cls in HYDRA_TYPE_TO_VALUE_CLASS.items()
}


def hydra_value_type(value: HydraValue) -> HydraType:
    return HYDRA_VALUE_CLASS_TO_TYPE[type(value)]


def wrap_value(value: Any) -> HydraValue:
    """Best-effort conversion for builtin Python values.

    This is intentionally conservative; explicit HydraValue wrappers should win
    whenever the caller cares about wire-level type selection.
    """

    if isinstance(value, HydraValue):
        return value
    if value is None:
        return HydraNone()
    if isinstance(value, bool):
        return HydraBool(value)
    if isinstance(value, int):
        return HydraInt64(value)
    if isinstance(value, float):
        return HydraFloat64(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return HydraBinary(bytes(value))
    if isinstance(value, _dt.datetime):
        return HydraDateTime(value)
    if isinstance(value, list):
        return HydraArray(list(value))
    if isinstance(value, tuple):
        return HydraArray(list(value))
    if isinstance(value, dict):
        return HydraHashMap(dict(value))
    return HydraUtf8(str(value))


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
    "HYDRA_TYPE_TO_VALUE_CLASS",
    "HYDRA_VALUE_CLASS_TO_TYPE",
    "hydra_value_type",
    "wrap_value",
]
