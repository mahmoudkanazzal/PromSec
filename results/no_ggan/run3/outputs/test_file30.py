# -*- coding: utf-8 -*-
"""Secure wrapper for the Server Density API.

Provides functions to create, delete, list, update devices and install the
Server Density agent while handling authentication via Salt pillars and
ensuring safe execution practices.
"""

import json
import logging
import os
import tempfile
import subprocess
import urllib.parse

import requests
from requests.exceptions import RequestException

log = logging.getLogger(__name__)
REQUEST_TIMEOUT = 10


def get_sd_auth(val, sd_auth_pillar_name='serverdensity'):
    """Retrieve authentication data from a Salt pillar.

    Args:
        val (str): The key to retrieve from the pillar.
        sd_auth_pillar_name (str): Name of the pillar containing auth data.

    Returns:
        The requested value from the pillar.

    Raises:
        salt.exceptions.CommandExecutionError: If the pillar or key is missing.
    """
    log.debug('Fetching auth value %s from pillar %s', val, sd_auth_pillar_name)
    pillar = __pillar__.get(sd_auth_pillar_name)
    if pillar is None:
        raise __import__('salt.exceptions').CommandExecutionError(
            f'Pillar "{sd_auth_pillar_name}" not found.'
        )
    if val not in pillar:
        raise __import__('salt.exceptions').CommandExecutionError(
            f'Key "{val}" not found in pillar "{sd_auth_pillar_name}".'
        )
    return pillar[val]


def _clean_salt_variables(params, variable_prefix="__"):
    """Return a new dict without keys that start with the given prefix."""
    return {k: v for k, v in params.items() if not k.startswith(variable_prefix)}


def _handle_response(response):
    """Process an HTTP response.

    Returns JSON data for a 200 status, otherwise logs a warning and returns None.

    Raises:
        salt.exceptions.CommandExecutionError: If JSON parsing fails.
    """
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            raise __import__('salt.exceptions').CommandExecutionError(
                f'Invalid JSON response: {response.text}'
            )
    log.warning('Unexpected status code %s: %s', response.status_code, response.text)
    return None


def create(name, **params):
    """Create a new device in Server Density.

    Args:
        name (str): Name of the device.
        **params: Additional device attributes.

    Returns:
        Parsed JSON response or None.

    Raises:
        salt.exceptions.CommandExecutionError: On request failures or auth errors.
    """
    log.debug('Creating device %s with params %s', name, params)
    payload = _clean_salt_variables(params)
    payload['name'] = name
    token = get_sd_auth('api_token')
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    url = 'https://api.serverdensity.io/inventory/devices/'
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
    except RequestException as exc:
        log.error('POST request failed: %s', exc)
        raise __import__('salt.exceptions').CommandExecutionError(str(exc))
    log.debug('Response status: %s', response.status_code)
    log.debug('Response text: %s', response.text)
    return _handle_response(response)


def delete(device_id):
    """Delete a device from Server Density.

    Args:
        device_id (str): Identifier of the device to delete.

    Returns:
        Parsed JSON response or None.

    Raises:
        salt.exceptions.CommandExecutionError: On request failures or auth errors.
    """
    encoded_id = urllib.parse.quote_plus(str(device_id))
    token = get_sd_auth('api_token')
    headers = {'Authorization': f'Bearer {token}'}
    url = f'https://api.serverdensity.io/inventory/devices/{encoded_id}'
    try:
        response = requests.delete(url, headers=headers, timeout=REQUEST_TIMEOUT)
    except RequestException as exc:
        log.error('DELETE request failed: %s', exc)
        raise __import__('salt.exceptions').CommandExecutionError(str(exc))
    log.debug('Response status: %s', response.status_code)
    log.debug('Response text: %s', response.text)
    return _handle_response(response)


def ls(**params):
    """List devices or resources from Server Density.

    Args:
        **params: Optional filter parameters.

    Returns:
        Parsed JSON response or None.

    Raises:
        salt.exceptions.CommandExecutionError: On request failures or auth errors.
    """
    cleaned = _clean_salt_variables(params)
    endpoint = 'devices' if not cleaned else 'resources'
    token = get_sd_auth('api_token')
    headers = {'Authorization': f'Bearer {token}'}
    url = f'https://api.serverdensity.io/inventory/{endpoint}'
    filters = {k: str(v) for k, v in cleaned.items()}
    query = {}
    if filters:
        query['filter'] = json.dumps(filters)
    try:
        response = requests.get(url, headers=headers, params=query, timeout=REQUEST_TIMEOUT)
    except RequestException as exc:
        log.error('GET request failed: %s', exc)
        raise __import__('salt.exceptions').CommandExecutionError(str(exc))
    log.debug('Response status: %s', response.status_code)
    log.debug('Response text: %s', response.text)
    return _handle_response(response)


def update(device_id, **params):
    """Update an existing device in Server Density.

    Args:
        device_id (str): Identifier of the device to update.
        **params: Fields to update.

    Returns:
        Parsed JSON response or None.

    Raises:
        salt.exceptions.CommandExecutionError: On request failures or auth errors.
    """
    cleaned = _clean_salt_variables(params)
    encoded_id = urllib.parse.quote_plus(str(device_id))
    token = get_sd_auth('api_token')
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    url = f'https://api.serverdensity.io/inventory/devices/{encoded_id}'
    try:
        response = requests.put(url, json=cleaned, headers=headers, timeout=REQUEST_TIMEOUT)
    except RequestException as exc:
        log.error('PUT request failed: %s', exc)
        raise __import__('salt.exceptions').CommandExecutionError(str(exc))
    log.debug('Response status: %s', response.status_code)
    log.debug('Response text: %s', response.text)
    return _handle_response(response)


def install_agent(agent_key):
    """Download and execute the Server Density agent installer.

    Args:
        agent_key (str): The agent key to register the installation.

    Returns:
        Stripped stdout from the installer script.

    Raises:
        salt.exceptions.CommandExecutionError: On validation, download,
            file, or execution errors.
    """
    account_url = get_sd_auth('account_url')
    if not isinstance(account_url, str) or not account_url:
        raise __import__('salt.exceptions').CommandExecutionError('account_url must be a non‑empty string.')
    parsed = urllib.parse.urlparse(account_url)
    if not parsed.scheme or not parsed.netloc:
        raise __import__('salt.exceptions').CommandExecutionError('account_url is not a valid URL.')
    script_url = 'https://www.serverdensity.com/downloads/agent-install.sh'
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            resp = requests.get(script_url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except RequestException as exc:
            log.error('Failed to download installer script: %s', exc)
            raise __import__('salt.exceptions').CommandExecutionError(str(exc))
        script_path = os.path.join(tmpdir, 'install.sh')
        try:
            with open(script_path, 'wb') as f:
                f.write(resp.content)
        except OSError as exc:
            log.error('Failed to write installer script: %s', exc)
            raise __import__('salt.exceptions').CommandExecutionError(str(exc))
        os.chmod(script_path, 0o700)
        try:
            result = subprocess.run(
                [script_path, '-a', account_url, '-k', agent_key],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                check=True,
                timeout=300
            )
        except subprocess.CalledProcessError as exc:
            log.error('Installer script failed: %s', exc)
            raise __import__('salt.exceptions').CommandExecutionError(
                f'Agent installation failed: {exc}'
            )
        except subprocess.TimeoutExpired as exc:
            log.error('Installer script timed out: %s', exc)
            raise __import__('salt.exceptions').CommandExecutionError('Agent installation timed out.')
        log.debug('Installer stdout: %s', result.stdout)
        return result.stdout.strip()