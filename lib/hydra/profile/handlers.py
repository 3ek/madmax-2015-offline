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
"""Profile CRUD handlers for the offline Hydra server."""

import struct

from ..codec import (
    HydraHashMap,
    HydraNone,
    HydraReader,
    HydraUInt64,
    HydraWriter,
)
from . import store as profile_store
from .fields import (
    DEFAULT_PLATFORM_FIELDS,
    effective_guid_value,
    normalize_requested_fields,
    profile_value_for_field,
)
from .time import current_game_time


_READER = HydraReader()
_WRITER = HydraWriter()


def _read_guid_and_fields(body: bytes) -> tuple[int, list[str]]:
    """Parse: [UINT64|INT64: guid] [ARRAY: field_name_strings]."""
    if len(body) < 9:
        return 0, []
    _, guid, pos = _READER.read_python(body, 0)
    guid = int(guid) if guid is not None else 0
    if pos >= len(body):
        return guid, []
    _, fields_raw, _ = _READER.read_python(body, pos)
    fields = normalize_requested_fields(fields_raw)
    return guid, fields


def _read_guid_and_struct(body: bytes) -> tuple[int, dict]:
    """Parse: [UINT64|INT64: guid] [STRUCT|HASHMAP: {field->value}]."""
    if len(body) < 9:
        return 0, {}
    _, guid, pos = _READER.read_python(body, 0)
    guid = int(guid) if guid is not None else 0
    if pos >= len(body):
        return guid, {}
    _, struct_val, _ = _READER.read_python(body, pos)
    if not isinstance(struct_val, dict):
        return guid, {}
    return guid, {str(k): v for k, v in struct_val.items()}


def _profile_by_guid(guid: int) -> tuple[str | None, dict | None]:
    """Lookup profile by numeric guid (== platform_account_id for Steam)."""
    guid_str = str(guid)
    if guid_str in profile_store.profiles:
        return guid_str, profile_store.profiles[guid_str]
    for pid, prof in profile_store.profiles.items():
        if str(prof.get("platform_account_id", "")) == guid_str:
            return pid, prof
    if profile_store.profiles:
        pid = next(iter(profile_store.profiles))
        return pid, profile_store.profiles[pid]
    return None, None


def _timestamp_response(profile: dict, fields: list[str]) -> bytes:
    return _WRITER.write(
        HydraHashMap({field: profile_value_for_field(profile, field) for field in fields})
    )


def handle_profile_get(body: bytes) -> bytes:
    """
    POST /profile/get
    Body: [UINT64: guid] [ARRAY: field_names]
    Response: [HASHMAP: {field -> UINT64 timestamp}]
    """
    guid, fields = _read_guid_and_fields(body)
    print(f"[HYDRA] profile/get  guid={guid}  fields={fields}")

    _, profile = _profile_by_guid(guid)
    if profile is None:
        return _WRITER.write(HydraHashMap({}))

    if not fields:
        fields = ["updated_at", "timestamp_scrap_rewarded"]
    resp = _timestamp_response(profile, fields)
    print(f"[HYDRA] profile/get  response {len(resp)}b  hex={resp.hex()}")
    return resp


def handle_profile_create(body: bytes) -> bytes:
    """
    POST /profile/create
    Body: [opcode byte] [STRUCT/HASHMAP: {field->value}] (KV pairs)
    Response: [UINT64: guid_as_steamid]
    """
    if not body:
        return _WRITER.write(HydraUInt64(0))

    inner = body[1:]
    if len(inner) < 4:
        return _WRITER.write(HydraUInt64(0))
    count = struct.unpack_from(">I", inner, 0)[0]
    pos = 4
    data: dict[str, object] = {}
    for _ in range(count):
        try:
            _, key, pos = _READER.read_python(inner, pos)
            _, val, pos = _READER.read_python(inner, pos)
            data[str(key)] = val
        except Exception:
            break

    platform_id = str(data.get("platform_account_id", ""))
    if not platform_id:
        return _WRITER.write(HydraUInt64(0))

    profile = profile_store.upsert_profile(platform_id, data)
    guid = effective_guid_value(profile)
    print(f"[HYDRA] profile/create  platform_id={platform_id}  guid={guid}")
    return _WRITER.write(HydraUInt64(guid))


def handle_profile_get_by_platform(body: bytes) -> bytes:
    """
    POST /profile/get_by_platform_account_id
    Body: [UTF8: platform_id] [ARRAY: field_names]
    Response: [HASHMAP: {field->value}]
    """
    _, platform_id, pos = _READER.read_python(body, 0)
    _, requested_fields, _ = _READER.read_python(body, pos)
    platform_id = str(platform_id)
    normalized_fields = normalize_requested_fields(requested_fields)

    profile = profile_store.profiles.get(platform_id)
    if profile is None or not profile.get("name"):
        print(f"[HYDRA] profile/get_by_platform  {platform_id} NOT FOUND (stub, no name)")
        return _WRITER.write(HydraHashMap({}))

    if not normalized_fields:
        normalized_fields = list(DEFAULT_PLATFORM_FIELDS)

    payload: dict[str, object] = {}
    for fname in normalized_fields:
        val = profile_value_for_field(profile, fname)
        if val is not None:
            payload[fname] = val

    resp = _WRITER.write(HydraHashMap(payload))
    print(f"[HYDRA] profile/get_by_platform  {platform_id}  {len(payload)} fields  {len(resp)}b")
    return resp


def handle_profile_update(inner: bytes) -> bytes:
    """
    POST /profile/update
    Body (inner, after outer offset strip): [UINT64: guid] [STRUCT: {field->value}]
    Response: [NONE] (ACK)
    """
    guid, updates = _read_guid_and_struct(inner)
    print(f"[HYDRA] profile/update  guid={guid}  keys={list(updates.keys())}")

    if not updates:
        return _WRITER.write(HydraNone())

    _, profile = _profile_by_guid(guid)
    if profile is None:
        return _WRITER.write(HydraNone())

    pid = str(profile.get("platform_account_id", "")) or next(iter(profile_store.profiles))
    safe_updates: dict[str, object] = {}
    for k, v in updates.items():
        if k in ("guid", "platform_account_id"):
            continue
        if k == "timestamp_scrap_rewarded":
            safe_updates[k] = str(current_game_time())
        elif isinstance(v, str):
            safe_updates[k] = v
        elif hasattr(v, "timestamp"):
            safe_updates[k] = int(v.timestamp())
        else:
            try:
                safe_updates[k] = int(v)
            except (TypeError, ValueError):
                safe_updates[k] = v
    profile_store.upsert_profile(pid, safe_updates)
    return _WRITER.write(HydraNone())


__all__ = [
    "handle_profile_create",
    "handle_profile_get",
    "handle_profile_get_by_platform",
    "handle_profile_update",
]
