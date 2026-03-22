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
"""Helpers for Turbine SOAP emulation."""

from .dispatch import handle_turbine_request, is_turbine_host
from .request_log import log_all_request, log_turbine_request

__all__ = ["handle_turbine_request", "is_turbine_host", "log_all_request", "log_turbine_request"]
