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
"""Auth handlers."""

from .codec import wrap_hex_body


def _varint(value: int) -> bytes:
    buf = []
    while True:
        byte = value & 0x7F
        value >>= 7
        buf.append(byte | 0x80 if value else byte)
        if not value:
            return bytes(buf)


def _field_varint(field: int, value: int) -> bytes:
    return _varint((field << 3) | 0) + _varint(value)


def handle_auth_pc_steam(wrapper_prefix: int, payload: bytes) -> bytes:
    del payload
    return wrap_hex_body(wrapper_prefix, _field_varint(1, 1))


def handle_heartbeat(wrapper_prefix: int, payload: bytes) -> bytes:
    del payload
    return wrap_hex_body(wrapper_prefix, _field_varint(1, 1))


def handle_spawn_error(wrapper_prefix: int, payload: bytes) -> bytes:
    del payload
    return wrap_hex_body(wrapper_prefix, _field_varint(1, 1))
