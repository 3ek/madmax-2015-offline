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
"""SOAP builders and method handlers for Turbine AMS endpoints."""

import re

AMS_NS = "http://www.turbine.com/SE/AMS"


def soap_envelope(body_inner: str) -> bytes:
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope'
        ' xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"'
        f' xmlns:ams="{AMS_NS}">'
        "<soap:Header/>"
        "<soap:Body>"
        + body_inner
        + "</soap:Body>"
        "</soap:Envelope>"
    ).encode("utf-8")


def xml(tag: str, text: str) -> str:
    return f"<ams:{tag}>{text}</ams:{tag}>"


def extract(body: bytes, tag: str) -> str:
    pattern = rb"<(?:ams:)?" + tag.encode() + rb">(.*?)</(?:ams:)?" + tag.encode() + rb">"
    match = re.search(pattern, body, re.DOTALL)
    return match.group(1).decode(errors="replace").strip() if match else ""


def stable_wb_email(seed: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._+-]", "", seed or "")
    return f"{cleaned or 'player'}@wbplay.local"


def handle_lookup_wbid(body: bytes) -> bytes:
    console_id = extract(body, "consoleId") or "0"
    realm = extract(body, "realm") or "STEAM"
    wb_email = f"{realm}_{console_id}@example.com"
    inner = (
        "<ams:LookupWbidResponse>"
        f"<ams:LookupWbidResult>{wb_email}</ams:LookupWbidResult>"
        "</ams:LookupWbidResponse>"
    )
    print(f"[TURBINE] LookupWbid  ConsoleId={console_id}  Realm={realm}  LookupWbidResult={wb_email}")
    return soap_envelope(inner)


def handle_get_subscription_information(body: bytes) -> bytes:
    raw_id = extract(body, "wbId") or extract(body, "consoleId") or "0"
    wbid_account_id = stable_wb_email(raw_id)
    inner = (
        "<ams:GetSubscriptionInformationResponse>"
        "<ams:GetSubscriptionInformationResult>"
        + xml("WbidAccountId", wbid_account_id)
        + xml("SubscriptionId", raw_id)
        + xml("AccountId", wbid_account_id)
        + "<ams:Entitlements></ams:Entitlements>"
        + "</ams:GetSubscriptionInformationResult>"
        "</ams:GetSubscriptionInformationResponse>"
    )
    print(
        "[TURBINE] GetSubscriptionInformation  "
        f"raw_id={raw_id} WbidAccountId={wbid_account_id} AccountId={wbid_account_id} "
        f"SubscriptionId={raw_id} Entitlements=empty (minimal shape)"
    )
    return soap_envelope(inner)


def handle_convert_third_party_ticket() -> bytes:
    print(f"[TURBINE] ConvertThirdPartyTicket result=true")
    return soap_envelope(
        "<ams:ConvertThirdPartyTicketWithProductResponse>"
        "<ams:ConvertThirdPartyTicketWithProductResult>false</ams:ConvertThirdPartyTicketWithProductResult>"
        "</ams:ConvertThirdPartyTicketWithProductResponse>")



def authenticate_and_associate_response() -> bytes:
    print("[TURBINE] AuthenticateAndAssociate result=true")
    return soap_envelope(
        "<ams:AuthenticateAndAssociateResponse>"
        "<ams:AuthenticateAndAssociateResult>true</ams:AuthenticateAndAssociateResult>"
        "</ams:AuthenticateAndAssociateResponse>"
    )


def generic_response(path: str, body: bytes, method: str) -> bytes:
    wb_id = extract(body, "consoleId") or re.search(rb"76561[0-9]{12}", body)
    if not isinstance(wb_id, str) and wb_id:
        wb_id = wb_id.group(0).decode()
    elif not wb_id:
        wb_id = "0"
    response_method = method or "Unknown"
    generic_email = stable_wb_email(str(wb_id))
    print(f"[TURBINE] {response_method} (generic)  wbEmail={generic_email}  path={path}")
    inner = (
        f"<ams:{response_method}Response>"
        f"<ams:{response_method}Result>"
        + xml("wbEmail", generic_email)
        + "<ams:ErrorCode>0</ams:ErrorCode>"
        + "<ams:ErrorMessage/>"
        + f"</ams:{response_method}Result>"
        f"</ams:{response_method}Response>"
    )
    return soap_envelope(inner)
