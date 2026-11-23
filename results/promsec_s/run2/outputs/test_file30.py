# -*- coding: utf-8 -*-
"""
Server Density API wrapper.

Version: 1.0.0
"""

from __future__ import annotations

import json
import logging
import shutil
import shlex
import tempfile
from typing import Any, Dict

import requests
from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)

def _mask(value: str, show: int = 4) -> str:
    """Return a masked representation of a secret."""
    if not value:
        return ""
    return f"{value[:show]}{'*' * (len(value) - show)}"

def get_sd_auth(val: str, sd_auth_pillar_name: str = "serverdensity") -> str:
    """
    Retrieve authentication data from the Salt pillar ``__pillar__``.

    :param str val: Key to retrieve from the pillar dictionary.
    :param str sd_auth_pillar_name: Pillar name that contains the auth dict.
    :returns: The requested authentication value.
    :rtype: str
    :raises CommandExecutionError: If the pillar or key is missing.
    """
    pillar = __pillar__.get(sd_auth_pillar_name)  # type: ignore[name-defined]
    if not isinstance(pillar, dict):
        raise CommandExecutionError(
            f"Pillar '{sd_auth_pillar_name}' is missing or not a dictionary."
        )
    if val not in pillar:
        raise CommandExecutionError(
            f"Key '{val}' not found in pillar '{sd_auth_pillar_name}'."
        )
    secret = pillar[val]
    log.debug("Retrieved auth key '%s' from pillar '%s'.", val, sd_auth_pillar_name)
    return secret

def _clean_salt_variables(params: Dict[str, Any], variable_prefix: str = "__") -> Dict[str, Any]:
    """
    Remove any keys from the ``params`` dict that start with ``variable_prefix``.

    :param dict params: Original parameters dictionary.
    :param str variable_prefix: Prefix identifying Salt variables.
    :returns: New dictionary without Salt‑specific keys.
    :rtype: dict
    """
    return {k: v for k, v in params.items() if not k.startswith(variable_prefix)}

def _handle_response(response: requests.Response) -> Any:
    """
    Process a ``requests.Response`` object.

    :param requests.Response response: The HTTP response.
    :returns: Parsed JSON content.
    :raises CommandExecutionError: On non‑200 status or JSON errors.
    """
    log.debug(
        "HTTP %s received, content length %s.",
        response.status_code,
        len(response.content),
    )
    if response.status_code != 200:
        raise CommandExecutionError(
            f"Server Density API returned status {response.status_code}."
        )
    try:
        return response.json()
    except json.JSONDecodeError as exc:
        raise CommandExecutionError("Failed to decode JSON response.") from exc

def create(name: str, **params: Any) -> Any:
    """
    Create a new device in Server Density.

    :param str name: Device name.
    :param dict params: Additional device attributes.
    :returns: Parsed JSON response from the API.
    :rtype: dict
    :raises CommandExecutionError: On request or parsing failures.
    """
    cleaned = _clean_salt_variables(params)
    cleaned["name"] = name
    token = get_sd_auth("api_token")
    url = "https://api.serverdensity.io/inventory/devices/"
    try:
        response = requests.post(
            url,
            data=cleaned,
            params={"token": token},
            timeout=10,
        )
        return _handle_response(response)
    except requests.RequestException as exc:
        raise CommandExecutionError("Failed to create device.") from exc

def delete(device_id: str) -> Any:
    """
    Delete a device from Server Density.

    :param str device_id: Identifier of the device to delete.
    :returns: Parsed JSON response from the API.
    :rtype: dict
    :raises CommandExecutionError: On request or parsing failures.
    """
    token = get_sd_auth("api_token")
    url = f"https://api.serverdensity.io/inventory/devices/{device_id}"
    try:
        response = requests.delete(url, params={"token": token}, timeout=10)
        return _handle_response(response)
    except requests.RequestException as exc:
        raise CommandExecutionError("Failed to delete device.") from exc

def ls(**params: Any) -> Any:
    """
    List devices or resources from Server Density.

    :param dict params: Optional filter parameters.
    :returns: Parsed JSON response from the API.
    :rtype: dict
    :raises CommandExecutionError: On request or parsing failures.
    """
    cleaned = _clean_salt_variables(params)
    endpoint = "devices" if cleaned else "resources"
    token = get_sd_auth("api_token")
    query: Dict[str, str] = {"token": token}
    if cleaned:
        filter_str = json.dumps({k: str(v) for k, v in cleaned.items()})
        query["filter"] = filter_str
    url = f"https://api.serverdensity.io/inventory/{endpoint}"
    try:
        response = requests.get(url, params=query, timeout=10)
        return _handle_response(response)
    except requests.RequestException as exc:
        raise CommandExecutionError("Failed to list items.") from exc

def update(device_id: str, **params: Any) -> Any:
    """
    Update an existing device in Server Density.

    :param str device_id: Identifier of the device to update.
    :param dict params: Fields to update.
    :returns: Parsed JSON response from the API.
    :rtype: dict
    :raises CommandExecutionError: On request or parsing failures.
    """
    cleaned = _clean_salt_variables(params)
    token = get_sd_auth("api_token")
    url = f"https://api.serverdensity.io/inventory/devices/{device_id}"
    try:
        response = requests.put(
            url,
            data=cleaned,
            params={"token": token},
            timeout=10,
        )
        return _handle_response(response)
    except requests.RequestException as exc:
        raise CommandExecutionError("Failed to update device.") from exc

def install_agent(agent_key: str) -> None:
    """
    Download and install the Server Density agent.

    :param str agent_key: Agent registration key.
    :raises CommandExecutionError: If any step of the installation fails.
    """
    tmp_dir = tempfile.mkdtemp()
    try:
        account_url = get_sd_auth("account_url")
        curl_cmd = f"curl -fsSL {shlex.quote(account_url)}/install.sh -o installer.sh"
        __salt__["cmd.run"](curl_cmd, cwd=tmp_dir)  # type: ignore[name-defined]
        __salt__["cmd.run"]("chmod +x installer.sh", cwd=tmp_dir)  # type: ignore[name-defined]
        install_cmd = f"./installer.sh {shlex.quote(account_url)} {shlex.quote(agent_key)}"
        __salt__["cmd.run"](install_cmd, cwd=tmp_dir)  # type: ignore[name-defined]
        log.info("Server Density agent installed successfully.")
    except Exception as exc:
        raise CommandExecutionError("Failed to install Server Density agent.") from exc
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)