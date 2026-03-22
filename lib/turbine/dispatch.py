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
"""Dispatch helpers for Turbine SOAP traffic."""

import re

from config import TURBINE_DOMAINS, domain_matches

from .request_log import log_turbine_request, log_turbine_xml
from .soap import (
    authenticate_and_associate_response,
    generic_response,
    handle_convert_third_party_ticket,
    handle_get_subscription_information,
    handle_lookup_wbid,
)


def is_turbine_host(host: str) -> bool:
    return domain_matches(host, TURBINE_DOMAINS)


def handle_turbine_request(method: str, path: str, headers_raw: str, body: bytes) -> tuple[int, bytes, str]:
    print(f"[TURBINE] {method} {path}  ({len(body)}b)  hex={body[:64].hex()}")
    log_turbine_xml(body)
    response = turbine_soap_response(path, body)
    log_turbine_request(path, headers_raw, body, response)
    print(f"[TURBINE] responded {len(response)}b")
    return 200, response, "text/xml; charset=utf-8"


def turbine_soap_response(path: str, body: bytes) -> bytes:
    method_match = re.search(rb"<soap:Body>\s*<ams:(\w+)", body)
    soap_method = method_match.group(1).decode() if method_match else ""
    if soap_method == "LookupWbid":
        return handle_lookup_wbid(body)
    if soap_method == "GetSubscriptionInformation":
        return handle_get_subscription_information(body)
    if soap_method == "ConvertThirdPartyTicketWithProduct":
        return handle_convert_third_party_ticket()
    if soap_method == "AuthenticateAndAssociate":
        return authenticate_and_associate_response()
    return generic_response(path, body, soap_method)
