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
"""Profile storage helpers."""

import json
from pathlib import Path

from ..codec import HydraReader

PROFILES_FILE = Path(__file__).resolve().parents[3] / "data" / "profiles.json"
profiles: dict[str, dict] = {}
_READER = HydraReader()


def load_profiles() -> None:
    if not PROFILES_FILE.exists():
        return
    try:
        profiles.update(json.loads(PROFILES_FILE.read_text(encoding="utf-8")))
    except Exception as exc:
        print(f"[HYDRA] WARNING: could not load profiles: {exc}")


def save_profiles() -> None:
    try:
        PROFILES_FILE.write_text(json.dumps(profiles, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"[HYDRA] WARNING: could not save profiles: {exc}")


def upsert_profile(platform_id: str, fields: dict | None = None) -> dict:
    profile = profiles.setdefault(platform_id, {"platform_account_id": platform_id})
    if fields:
        for key, value in fields.items():
            profile[str(key)] = value
    if platform_id and "platform_account_id" not in profile:
        profile["platform_account_id"] = platform_id
    save_profiles()
    return profile


def parse_profile_get_probe_body(body: bytes) -> tuple[str | None, list | None, str | None]:
    try:
        pos = 0
        _, platform_id, pos = _READER.read_python(body, pos)
        _, requested_fields, _ = _READER.read_python(body, pos)
        return str(platform_id), requested_fields, None
    except Exception as exc:
        return None, None, f"parse_error={exc}"


load_profiles()
