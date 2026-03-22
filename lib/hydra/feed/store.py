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
"""Feed datastore helpers for data/feeds/<CHANNEL>.json."""

import json
from pathlib import Path

FEEDS_DIR = Path(__file__).resolve().parents[3] / "data" / "feeds"


def _feed_path(channel: str) -> str:
    safe = channel.replace("/", "_").replace("\\", "_")
    return str(FEEDS_DIR / f"{safe}.json")


def load_feed(channel: str, requested_fields: list[str]) -> dict:
    """Load feed data for channel, auto-creating/updating file for missing fields."""
    FEEDS_DIR.mkdir(parents=True, exist_ok=True)
    path = _feed_path(channel)
    data: dict = {}
    if Path(path).exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            print(f"[FEED_STORE] Failed to load {path}: {exc}")
            data = {}
    changed = False
    for field in requested_fields:
        if field not in data:
            data[field] = ""
            changed = True
    if changed:
        _save_feed(path, data)
    return data


def save_feed(channel: str, data: dict) -> None:
    FEEDS_DIR.mkdir(parents=True, exist_ok=True)
    _save_feed(_feed_path(channel), data)


def _save_feed(path: str, data: dict) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        print(f"[FEED_STORE] Failed to save {path}: {exc}")
