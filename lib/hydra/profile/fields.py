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
"""Profile field mapping helpers."""

# timestamp_scrap_rewarded format confirmed from profile/update body:
#   0e 00000001 '0'  ->  TYPE_UTF8, value = string "0"
# The game stores and sends this field as a UTF-8 string, not a numeric type.
# Default "0" = oldest possible value -> maximum accumulated scrap on first login.

from datetime import datetime, timezone

from ..codec import HydraUInt64
from .time import current_game_time, game_time_to_datetime

INT32_MAX = 2147483647  # game computes elapsed = INT32_MAX - timestamp_scrap_rewarded

DEFAULT_PLATFORM_FIELDS = [
    "guid", "name", "wb_id", "wb_account_id", "wb_subscription_id", "dlcs", "age_group",
]


def normalize_requested_fields(requested_fields: object) -> list[str]:
    if isinstance(requested_fields, list):
        return [str(item) for item in requested_fields]
    if requested_fields is None:
        return []
    return [str(requested_fields)]


def effective_guid_value(profile: dict) -> int:
    platform_id = str(profile.get("platform_account_id") or "").strip()
    if platform_id.isdigit():
        return int(platform_id)
    try:
        return int(profile.get("guid", 1))
    except Exception:
        return 1


def profile_value_for_field(profile: dict, field: str) -> object:
    if field in {"guid", "id"}:
        return HydraUInt64(effective_guid_value(profile))
    if field == "timestamp_scrap_rewarded":
        # Game computes: elapsed_seconds = INT32_MAX - atoi(our_value)
        # We store last-reward time as YYYYMMDDHHmmss (written by game via profile/update).
        # On read: convert stored YYYYMMDDHHmmss -> INT32_MAX - elapsed_seconds_since_then
        # No stored timestamp -> return "0" (elapsed = INT32_MAX = max scrap, always pays out)
        stored = profile.get(field)
        if stored is None or str(stored) == "0":
            return "0"
        try:
            last_reward_dt = game_time_to_datetime(int(stored))
            now = datetime.now(timezone.utc)
            elapsed_seconds = int((now - last_reward_dt).total_seconds())
            value = max(0, INT32_MAX - elapsed_seconds)
            return str(value)
        except Exception:
            return "0"  # fallback: treat as never rewarded
    if field in {"updated_at", "timestamp_trigger"}:
        stored = profile.get(field)
        if stored is None:
            stored = current_game_time()
            profile[field] = stored
        return HydraUInt64(int(stored))
    if field == "name":
        return profile.get("display_name")
    if field in {"wb_id", "wb_account_id", "wb_subscription_id"}:
        # WB Games account fields - map to platform_account_id (SteamID) offline
        return str(effective_guid_value(profile))
    if field in {"display_name", "game_lang", "country_of_origin", "platform_account_id"}:
        return profile.get(field)
    if field == "dlcs":
        return profile.get("dlcs")
    if field == "age_group":
        return profile.get("age_group")
    return profile.get(field)
