# -*- coding: utf-8 -*-
"""Secure wrapper for the Server Density inventory API."""

import json
import urllib.parse
import logging as _logging
import re
import shlex
import requests
from salt.exceptions import CommandExecutionError

_logger = _logging.getLogger("serverdensity_wrapper")
if not _logger.handlers:
    _logger.addHandler(_logging.NullHandler())
_logger.propagate = False

_HTTP_TIMEOUT = 10

def get_sd_auth(val, sd_auth_pillar_name="serverdensity"):
    pillar = globals().get("__pillar__")
    if not isinstance(pillar, dict):
        raise CommandExecutionError("Global __pillar__ is not a dictionary.")
    if sd_auth_pillar_name not in pillar:
        raise CommandExecutionError(f"Pillar '{sd_auth_pillar_name}' not found.")
    auth_section = pillar.get(sd_auth_pillar_name)
    if not isinstance(auth_section, dict):
        raise CommandExecutionError(f"Pillar '{sd_auth_pillar_name}' is not a dictionary.")
    if val not in auth_section:
        raise CommandExecutionError(f"Key '{val}' not found in pillar '{sd_auth_pillar_name}'.")
    return auth_section[val]

def _clean_salt_variables(params, variable_prefix="__"):
    return {k: v for k, v in params.items() if not k.startswith(variable_prefix)}

def _validate_device_id(device_id):
    dev_str = str(device_id)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", dev_str):
        raise CommandExecutionError(f"Invalid device_id '{device_id}'.")
    return dev_str

def _validate_url(url):
    if not isinstance(url, str):
        raise CommandExecutionError("URL must be a string.")
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    if not re.fullmatch(pattern, url):
        raise CommandExecutionError(f"Invalid URL '{url}'.")
    return url

def _validate_agent_key(key):
    if not isinstance(key, str):
        raise CommandExecutionError("Agent key must be a string.")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", key):
        raise CommandExecutionError(f"Invalid agent key '{key}'.")
    return key

def create(name, **params):
    cleaned = _clean_salt_variables(params)
    payload = {"name": name, **cleaned}
    token = get_sd_auth("api_token")
    url = "https://api.serverdensity.io/inventory/devices/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    _logger.debug("POST %s payload=%s headers=%s", url, payload, headers)
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=_HTTP_TIMEOUT, verify=True)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise CommandExecutionError(f"Failed to create device: {exc}") from exc
    try:
        return response.json()
    except ValueError as exc:
        raise CommandExecutionError(f"Invalid JSON response: {exc}") from exc

def delete(device_id):
    dev = _validate_device_id(device_id)
    encoded = urllib.parse.quote(dev, safe="")
    base = "https://api.serverdensity.io/inventory/devices/"
    url = urllib.parse.urljoin(base, encoded)
    token = get_sd_auth("api_token")
    headers = {"Authorization": f"Bearer {token}"}
    _logger.debug("DELETE %s headers=%s", url, headers)
    try:
        response = requests.delete(url, headers=headers, timeout=_HTTP_TIMEOUT, verify=True)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise CommandExecutionError(f"Failed to delete device: {exc}") from exc
    try:
        return response.json()
    except ValueError as exc:
        raise CommandExecutionError(f"Invalid JSON response: {exc}") from exc

def ls(**params):
    cleaned = _clean_salt_variables(params)
    endpoint = "devices" if cleaned else "resources"
    base = f"https://api.serverdensity.io/inventory/{endpoint}"
    token = get_sd_auth("api_token")
    headers = {"Authorization": f"Bearer {token}"}
    if cleaned:
        query = urllib.parse.urlencode({"filter": json.dumps(cleaned)})
        url = f"{base}?{query}"
    else:
        url = base
    _logger.debug("GET %s headers=%s", url, headers)
    try:
        response = requests.get(url, headers=headers, timeout=_HTTP_TIMEOUT, verify=True)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise CommandExecutionError(f"Failed to list {endpoint}: {exc}") from exc
    try:
        return response.json()
    except ValueError as exc:
        raise CommandExecutionError(f"Invalid JSON response: {exc}") from exc

def update(device_id, **params):
    cleaned = _clean_salt_variables(params)
    dev = _validate_device_id(device_id)
    encoded = urllib.parse.quote(dev, safe="")
    base = "https://api.serverdensity.io/inventory/devices/"
    url = urllib.parse.urljoin(base, encoded)
    token = get_sd_auth("api_token")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    _logger.debug("PUT %s payload=%s headers=%s", url, cleaned, headers)
    try:
        response = requests.put(url, json=cleaned, headers=headers, timeout=_HTTP_TIMEOUT, verify=True)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise CommandExecutionError(f"Failed to update device: {exc}") from exc
    try:
        return response.json()
    except ValueError as exc:
        raise CommandExecutionError(f"Invalid JSON response: {exc}") from exc

def install_agent(agent_key):
    account_url = get_sd_auth("account_url")
    safe_account = _validate_url(account_url)
    safe_key = _validate_agent_key(agent_key)
    cmd_func = globals().get("__salt__", {}).get("cmd.run_all")
    if not callable(cmd_func):
        raise CommandExecutionError("cmd.run_all is not available.")
    commands = [
        ["curl", "-fsSL", "https://www.serverdensity.com/downloads/agent-install.sh", "-o", "/tmp/install.sh"],
        ["chmod", "+x", "/tmp/install.sh"],
        ["/tmp/install.sh", "-a", safe_account, "-k", safe_key]
    ]
    result = None
    for command in commands:
        cmd_str = shlex.join(command)
        _logger.debug("Executing command: %s", cmd_str)
        result = cmd_func(cmd_str)
        if not isinstance(result, dict):
            raise CommandExecutionError(f"Command execution did not return a dict: {result}")
        if result.get("retcode", 0) != 0:
            raise CommandExecutionError(f"Command failed: {result.get('stderr', '')}")
    if isinstance(result, dict) and "stdout" in result:
        return result["stdout"]
    return result