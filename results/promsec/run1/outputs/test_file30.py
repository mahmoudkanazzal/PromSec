"""Server Density API wrapper module.

.. versionadded:: 1.0.0
"""

from __future__ import annotations

import json
import logging
import shlex
import urllib.parse
from typing import Any, Dict, Optional

import requests
from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)

def get_sd_auth(val: str, sd_auth_pillar_name: str = "serverdensity") -> str:
    """
    Retrieve a Server Density authentication value from a Salt pillar.

    CLI Example:

    .. code-block:: bash

        salt '*' serverdensity.get_sd_auth api_token
    """
    pillar = __salt__["pillar.get"](sd_auth_pillar_name, {})
    if not isinstance(pillar, dict):
        msg = f"Pillar '{sd_auth_pillar_name}' is missing or not a dictionary."
        log.error(msg)
        raise CommandExecutionError(msg)
    if val not in pillar:
        msg = f"Key '{val}' not found in pillar '{sd_auth_pillar_name}'."
        log.error(msg)
        raise CommandExecutionError(msg)
    token = pillar[val]
    log.debug("Retrieved auth value for %s from pillar %s", val, sd_auth_pillar_name)
    return token

def _clean_salt_variables(params: Dict[str, Any], variable_prefix: str = "__") -> Dict[str, Any]:
    """
    Remove Salt-specific variables from a dictionary.

    CLI Example:

    .. code-block:: bash

        salt '*' serverdensity._clean_salt_variables '{"__foo": "bar", "name": "device"}'
    """
    cleaned = {k: v for k, v in params.items() if not k.startswith(variable_prefix)}
    log.debug("Cleaned parameters: %s", cleaned)
    return cleaned

def create(name: str, **params: Any) -> Optional[Dict[str, Any]]:
    """
    Create a new device in Server Density.

    CLI Example:

    .. code-block:: bash

        salt '*' serverdensity.create my_device hostname=host1 ip=10.0.0.1
    """
    token = get_sd_auth("api_token")
    url = "https://api.serverdensity.io/inventory/devices/"
    data = _clean_salt_variables(params)
    data["name"] = name
    log.debug("Creating device with data: %s", data)
    try:
        response = requests.post(url, params={"token": token}, json=data, timeout=30)
    except requests.RequestException as exc:
        log.error("HTTP request failed: %s", exc)
        raise CommandExecutionError(f"Failed to create device: {exc}")
    log.debug("Response status: %s", response.status_code)
    if response.status_code != 200:
        log.error("Unexpected status code %s", response.status_code)
        return None
    try:
        result = response.json()
    except (json.JSONDecodeError, ValueError) as exc:
        log.error("JSON decode error: %s", exc)
        raise CommandExecutionError(f"Failed to parse JSON response: {exc}")
    log.debug("Create response JSON: %s", result)
    return result

def delete(device_id: str) -> Optional[Dict[str, Any]]:
    """
    Delete a device from Server Density.

    CLI Example:

    .. code-block:: bash

        salt '*' serverdensity.delete 12345
    """
    token = get_sd_auth("api_token")
    safe_id = urllib.parse.quote(device_id, safe="")
    url = f"https://api.serverdensity.io/inventory/devices/{safe_id}"
    log.debug("Deleting device with ID: %s", safe_id)
    try:
        response = requests.delete(url, params={"token": token}, timeout=30)
    except requests.RequestException as exc:
        log.error("HTTP request failed: %s", exc)
        raise CommandExecutionError(f"Failed to delete device: {exc}")
    log.debug("Response status: %s", response.status_code)
    if response.status_code != 200:
        log.error("Unexpected status code %s", response.status_code)
        return None
    try:
        result = response.json()
    except (json.JSONDecodeError, ValueError) as exc:
        log.error("JSON decode error: %s", exc)
        raise CommandExecutionError(f"Failed to parse JSON response: {exc}")
    log.debug("Delete response JSON: %s", result)
    return result

def ls(**params: Any) -> Optional[Dict[str, Any]]:
    """
    List devices or resources from Server Density.

    CLI Example:

    .. code-block:: bash

        salt '*' serverdensity.ls
        salt '*' serverdensity.ls hostname=host1
    """
    token = get_sd_auth("api_token")
    cleaned = _clean_salt_variables(params)
    endpoint = "devices" if not cleaned else "resources"
    url = f"https://api.serverdensity.io/inventory/{endpoint}/"
    filter_param = json.dumps({k: str(v) for k, v in cleaned.items()})
    log.debug("Listing %s with filter: %s", endpoint, filter_param)
    try:
        response = requests.get(
            url,
            params={"token": token, "filter": filter_param},
            timeout=30,
        )
    except requests.RequestException as exc:
        log.error("HTTP request failed: %s", exc)
        raise CommandExecutionError(f"Failed to list {endpoint}: {exc}")
    log.debug("Response status: %s", response.status_code)
    if response.status_code != 200:
        log.error("Unexpected status code %s", response.status_code)
        return None
    try:
        result = response.json()
    except (json.JSONDecodeError, ValueError) as exc:
        log.error("JSON decode error: %s", exc)
        raise CommandExecutionError(f"Failed to parse JSON response: {exc}")
    log.debug("List response JSON: %s", result)
    return result

def update(device_id: str, **params: Any) -> Optional[Dict[str, Any]]:
    """
    Update an existing device in Server Density.

    CLI Example:

    .. code-block:: bash

        salt '*' serverdensity.update 12345 hostname=newhost
    """
    token = get_sd_auth("api_token")
    safe_id = urllib.parse.quote(device_id, safe="")
    url = f"https://api.serverdensity.io/inventory/devices/{safe_id}"
    data = _clean_salt_variables(params)
    log.debug("Updating device %s with data: %s", safe_id, data)
    try:
        response = requests.put(url, params={"token": token}, json=data, timeout=30)
    except requests.RequestException as exc:
        log.error("HTTP request failed: %s", exc)
        raise CommandExecutionError(f"Failed to update device: {exc}")
    log.debug("Response status: %s", response.status_code)
    if response.status_code != 200:
        log.error("Unexpected status code %s", response.status_code)
        return None
    try:
        result = response.json()
    except (json.JSONDecodeError, ValueError) as exc:
        log.error("JSON decode error: %s", exc)
        raise CommandExecutionError(f"Failed to parse JSON response: {exc}")
    log.debug("Update response JSON: %s", result)
    return result

def install_agent(agent_key: str) -> None:
    """
    Install the Server Density agent on the local host.

    CLI Example:

    .. code-block:: bash

        salt '*' serverdensity.install_agent <agent_key>
    """
    account_url = get_sd_auth("account_url")
    installer_path = "/tmp/install.sh"
    curl_cmd = f"curl -sSL -o {shlex.quote(installer_path)} https://install.serverdensity.io/install.sh"
    chmod_cmd = f"chmod +x {shlex.quote(installer_path)}"
    run_cmd = f"{shlex.quote(installer_path)} -a {shlex.quote(account_url)} -k {shlex.quote(agent_key)}"
    log.debug("Downloading installer script")
    __salt__["cmd.run"](curl_cmd, python_shell=False)
    log.debug("Making installer executable")
    __salt__["cmd.run"](chmod_cmd, python_shell=False)
    log.debug("Running installer with account URL and agent key")
    __salt__["cmd.run"](run_cmd, python_shell=False)