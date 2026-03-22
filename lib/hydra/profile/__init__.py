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
"""Hydra profile helpers."""

from .handlers import (
    handle_profile_create,
    handle_profile_get,
    handle_profile_get_by_platform,
    handle_profile_update,
)
from .store import (
    load_profiles,
    parse_profile_get_probe_body,
    profiles,
    save_profiles,
    upsert_profile,
)

__all__ = [
    "handle_profile_create",
    "handle_profile_get",
    "handle_profile_get_by_platform",
    "handle_profile_update",
    "load_profiles",
    "parse_profile_get_probe_body",
    "profiles",
    "save_profiles",
    "upsert_profile",
]
