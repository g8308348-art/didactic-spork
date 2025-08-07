import os
import json
import logging
import subprocess
import shlex


def retrieve_password(username: str) -> str | None:
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
    auth_type = os.getenv("CYBERARK_AUTH_TYPE", "negotiate")

    if not all([api_url, app_id, username]):
        logging.debug("CyberArk variables missing; skipping dynamic password retrieval.")
        return None

    curl_cmd = (
        f'curl -k -s -X GET "{api_url}?AppID={app_id}&Object={username}" '
        f'-u : --{auth_type}'
    )

    try:
        result = subprocess.run(
            shlex.split(curl_cmd),
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        )
        data = json.loads(result.stdout or "{}")
        # CyberArk returns an object with a "Content" key containing the password
        if isinstance(data, dict):
            return data.get("Content") or data.get("password")
    except (subprocess.SubprocessError, json.JSONDecodeError, ValueError) as exc:
        logging.warning("Could not retrieve password from CyberArk: %s", exc)
    return None
