from typing import Optional
import os
import json
import logging

import requests

try:
    from requests_kerberos import HTTPKerberosAuth, DISABLED  # type: ignore
    _KERBEROS_AUTH = HTTPKerberosAuth(mutual_authentication=DISABLED)
except ImportError:
    # requests_kerberos is optional; if not available we'll attempt unauthenticated
    _KERBEROS_AUTH = None


def retrieve_password(username: str) -> Optional[str]:
    """Retrieve the password for *username* from CyberArk.

    This helper relies on the following environment variables being set:
        CYBERARK_API_URL   - Base URL for the CyberArk CCP endpoint (e.g. https://cyberark-cep.statestreet.com/ATMD/api)
        CYBERARK_APP_ID    - CyberArk application ID authorised to fetch credentials
        CYBERARK_SAFE      - Safe name where the account is stored
        CYBERARK_AUTH_TYPE - Authentication scheme to use with curl (defaults to "negotiate")

    It performs a `curl` call using negotiate/Kerberos authentication and returns
    the account password if the request succeeds, otherwise *None*.
    """
    api_url = os.getenv("CYBERARK_API_URL", "https://cyberark-ccp.statestreet.com/AIM/api/Accounts")
    app_id = os.getenv("CYBERARK_APP_ID", "")
    if not all([api_url, app_id, username]):
        logging.debug("CyberArk variables missing; skipping dynamic password retrieval.")
        return None

    url = f"{api_url}?AppID={app_id}&Object={username}"

    try:
        kwargs = {"verify": False, "timeout": 20}
        if _KERBEROS_AUTH is not None:
            kwargs["auth"] = _KERBEROS_AUTH
        resp = requests.get(url, **kwargs)
        resp.raise_for_status()
        data = resp.json()
        # CyberArk returns an object with a "Content" key containing the password
        if isinstance(data, dict):
            return data.get("Content") or data.get("password")
    except (requests.RequestException, json.JSONDecodeError, ValueError) as exc:
        logging.warning("Could not retrieve password from CyberArk: %s", exc)
    return None
